# coding: utf-8

import licant.util
import threading
import types
import inspect
from enum import Enum
import re
from functools import partial
import random
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
            # access optimization by lazy technique
            self._targets[tgt] = self._targets[licant.util.canonical_path(tgt)]
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
        if tgt in self.depends_as_set_lazy_cache:
            return self.depends_as_set_lazy_cache[tgt]

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

    def routine_do(self, func=None, deps=[], update_if=lambda s: False, tgt=None):
        self.add(Routine(func=func, deps=deps, update_if=update_if, tgt=tgt))
        return func

    def routine(self, func=None, **kwargs):
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

    def __init__(self, tgt, deps=[], action=lambda s: None, need_if=lambda s: True, weakdeps=[], actions=None, __help__=None, **kwargs):
        self.tgt = tgt
        deps = [self.to_name_if_needed(dep) for dep in deps]
        deps = self.expand_globs(deps)
        self.deps = deps
        self.need_if = need_if
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
        need = self.need_if(self)
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
        need_if=None,
        default_action="recurse_update_get_args",
        ** kwargs
    ):
        Target.__init__(self, tgt, deps,
                        default_action=default_action, **kwargs)
        self.need_if = need_if

    def recurse_update_get_args(self):
        return self.recurse_update(threads=self.core.runtime["threads"])

    def update(self, *args, **kwargs):
        return True

    def recursive_update_needed_request(self):
        if self.need_to_update():
            return True

        for dep in self.get_deplist():
            if dep.recursive_update_needed_request():
                return True

        return False

    def has_updated_depends(self):
        alldeps = self.core.depends_as_set(self, incroot=False)
        alldeps = [self.core.get(d) for d in alldeps]

        for d in alldeps:
            if (
                not isinstance(d, UpdatableTarget)
            ):
                raise Exception("Nonupdateble target used: {}".format(d))

        for d in alldeps:
            if d.need_to_update():
                return True

        return False

    def invoke_function_or_method(self, act):
        if isinstance(act, types.MethodType):
            return act()
        else:
            return act(self)

    def internal_need_if(self):
        return False

    def need_to_update(self):
        if self.need_if is not None:
            return self.need_if(self)
        else:
            return self.internal_need_if()

    def update_if_need(self):
        if self.recursive_update_needed_request():
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
                   "recurse_update_get_args", "update", "actlist"}

    def __init__(self,
                 func,
                 deps=[],
                 default_action="update",
                 update_if=lambda s: False,
                 tgt=None,
                 **kwargs):
        if tgt is None:
            tgt = func.__name__
        UpdatableTarget.__init__(self, tgt=tgt, deps=deps,
                                 default_action=default_action, **kwargs)
        self.func = func
        self.update_if = update_if
        self.args = []

    def update(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def self_need(self):
        return self.update_if(self)

    def recurse_update(self, *args, **kwargs):
        self.args = args
        super().recurse_update(**kwargs)


def routine_decorator_do(func=None, deps=[], update_if=lambda s: False, tgt=None, core=default_core()):
    core.add(Routine(func=func, deps=deps, update_if=update_if, tgt=tgt))
    return func


def routine_decorator(func=None, **kwargs):
    if inspect.isfunction(func):
        return routine_decorator_do(func, **kwargs)
    else:
        def decorator(func):
            return routine_decorator_do(func, **kwargs)
        return decorator


# def print_targets_list(target, *args):
#     if core.runtime["debug"]:
#         print("print_targets_list args:{}".format(args))

#     if len(core.targets) == 0:
#         print("targets doesn't founded")
#         return

#     keys = sorted(core.targets.keys())

#     if len(args) > 0:
#         keys = [m for m in keys if re.search(args[0], m)]

#     for k in keys:
#         print(k)


# def print_target_info(taget, *args):
#     if len(args) == 0:
#         licant.error("Need target mnemo")

#     print("name:", core.get(args[0]))
#     print("deps:", sorted(core.get(args[0]).deps))


# def print_deps(taget, *args):
#     if len(args) == 0:
#         name = licant.cli.default_target
#     else:
#         name = args[0]

#     lst = sorted(core.depends_as_set(name))
#     for l in lst:
#         print(l)


# def print_subtree(target, tgt):
#     print(core.subtree(tgt))


# corediag_target = Target(
#     tgt="corediag",
#     deps=[],
#     targets=print_targets_list,
#     tgtinfo=print_target_info,
#     subtree=print_subtree,
#     printdeps=print_deps,
#     actions={"targets", "tgtinfo", "subtree", "printdeps"},
#     __help__="Core state info",
# )

# default_core().add(corediag_target)


def do(target, action=None, args=[], kwargs={}):
    default_core().do(target=target, action=action, args=args, kwargs=kwargs)


def get_target(name):
    return default_core().get(name)


core = default_core()
