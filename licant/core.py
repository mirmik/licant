# coding: utf-8

import licant.util
import types
import inspect
from functools import partial
import glob
import os
from licant.solver import DependableTarget, InverseRecursiveSolver


class WrongAction(Exception):
    def __init__(self, obj, actname):
        self.obj = obj
        self.actname = actname

    def __str__(self):
        return "WrongAction: obj:{} actname:{} class:{} dict:{self.obj.__dict__}".format(self.obj, self.actname, self.obj.__class__, self.obj.__dict__)


class NoneDictionary(dict):
    def __init__(self):
        dict.__init__(self)

    def __getitem__(self, idx):
        try:
            return dict.__getitem__(self, idx)
        except Exception:
            return None


class Core:
    def __init__(self, debug=False):
        self._targets = {}
        self.help_showed_targets = []
        self.runtime = NoneDictionary()
        self.debug = debug
        self.depends_as_set_lazy_cache = {}

    def nullify_update_needity(self):
        if self.trace_mode():
            print("[Trace] nullify_update_needity phase.")
        for target in self._targets.values():
            target.nullify_update_needity()

    def evaluate_update_needity(self):
        if self.trace_mode():
            print("[Trace] evaluate_update_needity phase.")
        for target in self._targets.values():
            target.evaluate_update_needity()

    def update_update_needity(self):
        self.nullify_update_needity()
        self.evaluate_update_needity()

    def trace_mode(self):
        return self.runtime["trace"]

    def exist(self, name):
        return self.has(name)

    def add(self, target):
        """Add new target"""
        target.core = self
        self._targets[target.tgt] = target

        if self.debug:
            print("add target: " + target.tgt)

        if target.__help__ is not None:
            self.help_showed_targets.append(target)

        return target

    def get(self, tgt):
        """Get target object"""

        if str(tgt) in self._targets:
            return self._targets[str(tgt)]

        if licant.util.canonical_path(tgt) in self._targets:
            return self._targets[licant.util.canonical_path(tgt)]

        licant.util.error("unregistred target " + licant.util.yellow(tgt))

    def has(self, tgt):
        """Check if target exists"""
        if tgt in self._targets:
            return True

        if licant.util.canonical_path(tgt) in self._targets:
            # access optimization by lazy technique
            self._targets[tgt] = self._targets[licant.util.canonical_path(tgt)]
            return True

        return False

    def depends_as_set_impl(self, tgt, accum):
        target = self.get(str(tgt))
        for d in target.deps:
            if d not in accum:
                accum.add(d)
                self.depends_as_set_impl(d, accum)

    def depends_as_set(self, tgt, incroot):
        if (tgt, incroot) in self.depends_as_set_lazy_cache:
            return self.depends_as_set_lazy_cache[(tgt, incroot)]

        accumulator = set()
        if incroot:
            accumulator.add(str(tgt))
        self.depends_as_set_impl(tgt, accumulator)

        ret = sorted(accumulator)
        self.depends_as_set_lazy_cache[tgt] = ret
        return ret

    def target(self, name, deps=[], **kwargs):
        """Create new target"""
        return self.add(Target(name, deps=deps, **kwargs))

    def updtarget(self, name, deps=[], **kwargs):
        """Create new target"""
        return self.add(UpdatableTarget(name, deps=deps, **kwargs))

    def do(self, target, action=None, args=[], kwargs={}):
        """Do action on target"""
        if isinstance(target, str):
            target = self.get(target)

        if isinstance(target, (list, tuple)):
            for t in target:
                self.do(t, action, args, kwargs)
            return

        if action is None:
            action = target.default_action

        target.invoke(action, args=args, kwargs=kwargs)

    def routine_do(self, func=None, deps=[], update_if=lambda s: True, tgt=None):
        self.add(Routine(func=func, deps=deps, update_if=update_if, tgt=tgt))
        return func

    def routine(self, func=None, **kwargs):
        """Декоратор для создания обновляемых утилит. По умолчанию обновляется
        всегда. Если нужно обновлять только при изменении зависимостей, следует
        установить флаг dependable. Кастомную логику обновления можно задать
        через update_if.

        @param func: функция, которая будет вызываться при обновлении
        @param deps: список зависимостей
        @param update_if: функция, которая будет вызываться для проверки
            необходимости обновления. Если она вернет True, то будет вызвана
            функция func.
        @param tgt: имя цели. Если не задано, то будет использовано имя функции.
        @param core: ядро, в которое будет добавлена цель."""

        if inspect.isfunction(func):
            return self.routine_do(func, **kwargs)
        else:
            def decorator(func):
                return self.routine_do(func, **kwargs)
            return decorator


_default_core = Core()


def default_core():
    return _default_core


class Target:
    __actions__ = {"actlist", "print", "dependies"}

    def __init__(self,
                 tgt,
                 deps=[],
                 action=lambda s: None,
                 update_if=lambda s: True,
                 weakdeps=[],
                 actions=None,
                 __help__=None,
                 **kwargs):
        self.tgt = tgt
        deps = [self.to_name_if_needed(dep) for dep in deps]
        deps = self.expand_globs(deps)
        self.deps = deps
        self.update_if = update_if
        self.weakdeps = set(weakdeps)
        self.action = action
        self.default_action = "action"
        for k, v in kwargs.items():
            setattr(self, k, v)

        if actions is not None:
            self.__actions__ = self.__actions__.union(set(actions))

        self.__help__ = __help__

        self.need_by_self = None
        self.need_by_deps = None
        self.cached_deplist = None

    def to_name_if_needed(self, dep):
        if isinstance(dep, Target):
            return dep.tgt
        else:
            return dep

    def evaluate_update_needity(self):
        pass

    def nullify_update_needity(self):
        pass

    def trace_mode(self):
        return self.core.trace_mode()

    def dependies(self):
        print(self.deps)

    def name(self):
        return self.tgt

    def is_file(self):
        return False

    def expand_globs(self, deps):
        import licant.make
        ret = []
        for d in deps:
            if "*" in d:
                ret.extend(glob.glob(d))
            else:
                ret.append(d)
        for r in ret:
            if os.path.exists(r):
                licant.make.source(r)
        return ret

    def action_if_need(self):
        need = self.update_if(self)
        self.need_by_self = need
        if need:
            self.action(self)

    def get_deplist(self):
        if self.cached_deplist is None:
            self.cached_deplist = [self.core.get(d) for d in self.deps]

        return self.cached_deplist

    def actlist(self):
        print(licant.util.get_actions(self))

    def print(self):
        print(self.__dict__)

    def hasaction(self, act):
        return act in self.__actions__

    def invoke(self, funcname: str, args=[], critical: bool = False, kwargs={}):
        """Invoke func function or method, or mthod with func name for this target

                Поддерживается несколько разных типов func.
                В качестве func может быть вызвана внешняя функция с параметром текущей цели,
                или название локального метода.
                critical -- Действует для строкового вызова. Если данный attr отсутствует у цели,
                то в зависимости от данного параметра может быть возвращен None или выброшено исключение.

                TODO: Насколько я понимаю, critical более не используется.
                """
        if self.core.runtime["trace"]:
            print(
                "TRACE: Invoke: tgt:{}, act:{}, args:{}, kwargs:{}".format(
                    self.tgt, funcname, args, kwargs
                )
            )

        # Любое действия предверяется расчётом нужности обновления
        # выполняемой глобально для всего ядра
        self.core.update_update_needity()

        func = getattr(self, funcname, None)
        if func is None:
            if critical:
                print("wrong action: {}".format(funcname))
                raise WrongAction(self, funcname)
            return None

        if isinstance(func, types.MethodType):
            return func(*args, **kwargs)

        else:
            return func(self, *args, **kwargs)

    def __repr__(self):
        """По умолчанию вывод Target на печать возвращает идентификатор цели"""
        return self.tgt


class UpdatableTarget(Target):
    __actions__ = Target.__actions__.union(
        {"recurse_update", "recurse_update_get_args", "update", "update_if_need"}
    )

    def __init__(
        self,
        tgt,
        deps,
        update_if=lambda s: False,
        default_action="recurse_update_get_args",
        ** kwargs
    ):
        Target.__init__(self, tgt, deps,
                        default_action=default_action, **kwargs)
        self.update_if = update_if
        self.need_update = None

    def evaluate_update_needity(self):
        self.need_update = self.recursive_update_needed_request()
        if self.trace_mode():
            print("[Trace] update_needity: {} {}".format(self.tgt, self.need_update))

    def nullify_update_needity(self):
        self.need_update = None

    def recurse_update_get_args(self):
        return self.recurse_update(threads=self.core.runtime["threads"])

    def update(self, *args, **kwargs):
        return True

    def recursive_update_needed_request(self):
        if self.need_update is not None:
            return self.need_update

        if self.update_if(self):
            return True

        for dep in self.get_deplist():
            if dep.recursive_update_needed_request():
                return True

        return False

    def invoke_function_or_method(self, act):
        if isinstance(act, types.MethodType):
            return act()
        else:
            return act(self)

    def update_if_need(self):
        if self.need_update is None:
            raise Exception("need_update is None")

        if self.need_update:
            return self.invoke_function_or_method(self.update)
        else:
            return True

    def recurse_update(self, threads=1):
        if "threads" in self.core.runtime:
            threads = self.core.runtime["threads"]

        depset = self.core.depends_as_set(self, incroot=True)

        # It is set! It is not list because we need to remove repeated elements
        # from it. In can be repeated because of deps in target is not strong
        # one target have different names.
        depset = {self.core.get(d) for d in depset}

        curdep = None
        dtargets = []
        for d in depset:
            def what_to_do(d):
                return d.update_if_need()
            # Это нужно для корректной обработки путей файлов.
            deps_as_targets_names = [self.core.get(d).tgt for d in d.deps]
            dtgt = DependableTarget(name=d.tgt,
                                    deps=deps_as_targets_names,
                                    what_to_do=partial(what_to_do, d),
                                    args=[],
                                    kwargs={})
            dtargets.append(dtgt)
            if d.tgt == self.tgt:
                curdep = dtgt

        success = InverseRecursiveSolver(dtargets, count_of_threads=threads,
                                         trace=self.core.runtime["trace"]).exec()
        if success:
            assert curdep.is_done()
        return success


class Routine(UpdatableTarget):
    __actions__ = {"recurse_update",
                   "recurse_update_get_args", "invoke_routine" "update", "actlist"}

    def __init__(self,
                 func,
                 update_if,
                 deps=[],
                 default_action="invoke_routine",
                 tgt=None,
                 **kwargs):
        if tgt is None:
            tgt = func.__name__
        UpdatableTarget.__init__(self, tgt=tgt, deps=deps,
                                 default_action=default_action,
                                 update_if=update_if,
                                 **kwargs)
        self.func = func
        self.args = []

    def update(self):
        return self.func(*self.args)

    def invoke_routine(self, *args, threads=1, **kwargs):
        self.args = list(args)
        self.recurse_update(threads=threads)


def routine(func=None, **kwargs):
    return default_core().routine(func=func, **kwargs)


def do(target, action=None, args=[], kwargs={}):
    default_core().do(target=target, action=action, args=args, kwargs=kwargs)


def get_target(name):
    return default_core().get(name)


core = default_core()
