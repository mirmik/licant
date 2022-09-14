# coding: utf-8

import licant.util
import threading
import types
import inspect
from enum import Enum
import re
import random
import glob
import os


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
        self.targets = {}
        self.help_showed_targets = []
        self.runtime = NoneDictionary()
        self.debug = debug

    def exist(self, name):
        return name in self.targets

    def add(self, target):
        """Add new target"""
        target.core = self
        self.targets[target.tgt] = target

        if self.debug:
            print("add target: " + target.tgt)

        if target.__help__ is not None:
            self.help_showed_targets.append(target)

        return target

    def get(self, tgt):
        """Get target object"""
        if str(tgt) in self.targets:
            return self.targets[str(tgt)]
        licant.util.error("unregistred target " + licant.util.yellow(tgt))

    def has(self, tgt):
        """Check if target exists"""
        return tgt in self.targets

    def subtree(self, root):
        """Construct Subtree accessor for root target"""
        return SubTree(root=root, core=self)

    def depends_as_set(self, tgt, incroot=True):
        """TODO: as_set, but list returned???"""
        res = set()
        if incroot:
            res.add(str(tgt))

        target = self.get(str(tgt))

        for d in target.deps:
            if d not in res:
                res.add(d)
                subres = self.depends_as_set(d)
                res = res.union(subres)
        return sorted(res)

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


# Объект ядра с которым библиотеки работают по умолчанию.
core = Core()


class SubTree:
    def __init__(self, core, root):
        self.root = root
        self.core = core
        self.depset = core.depends_as_set(root)
        self.weakdepsset = list(self.core.get(root).weakdeps)

    def invoke_foreach(self, ops, cond=licant.util.always_true):
        if core.runtime["debug"]:
            print("FOREACH(root={}, ops={}, cond={})".format(self.root, ops, cond))

        sum = 0
        ret = None

        for d in self.depset + self.weakdepsset:
            target = self.core.get(d)
            if cond(target):
                ret = target.invoke(ops)

            if ret is not None:
                sum += 1

        return sum

    def __generate_rdepends_lists(self, targets):
        for t in targets:
            t.rdepends = []
            t.rcounter = 0

        for t in targets:
            for dname in t.deps:
                dtarget = self.core.get(dname)
                dtarget.rdepends.append(t.tgt)

    def generate_rdepends(self):
        targets = [self.core.get(t) for t in self.depset]
        self.__generate_rdepends_lists(targets)

    def reverse_recurse_invoke_single(
        self, ops, threads=None, cond=licant.util.always_true
    ):
        if core.runtime["trace"]:
            print(
                "SINGLETHREAD MODE(root={}, ops={}, cond={})".format(
                    self.root, ops, cond
                )
            )
        targets = [self.core.get(t) for t in self.depset]

        self.__generate_rdepends_lists(targets)

        works = licant.util.queue()

        for t in targets:
            if t.rcounter == len(t.deps):
                works.put(t)

        while not works.empty():
            w = works.get()

            if cond(w):
                ret = w.invoke(ops)
                if ret is False:
                    print(licant.util.red("runtime error"))
                    exit(-1)

            for r in [self.core.get(t) for t in w.rdepends]:
                r.rcounter = r.rcounter + 1
                if r.rcounter == len(r.deps):
                    works.put(r)

    def reverse_recurse_invoke_threads(
        self, ops, threads, cond=licant.util.always_true
    ):
        if core.runtime["trace"]:
            print(
                "MULTITHREAD MODE(root={}, threads={}, ops={}, cond={})".format(
                    self.root, threads, ops, cond
                )
            )

        targets = [self.core.get(t) for t in self.depset]

        self.__generate_rdepends_lists(targets)
        works = licant.util.queue()

        class info_cls:
            def __init__(self):
                self.have_done = 0
                self.need_done = len(targets)
                self.sum = 0
                self.err = False

        info = info_cls()

        for t in targets:
            if t.rcounter == len(t.deps):
                works.put(t)

        lock = threading.Lock()

        def thread_func(index):
            while info.have_done != info.need_done:
                if info.err:
                    break

                lock.acquire()
                if not works.empty():
                    w = works.get()
                    lock.release()

                    if core.runtime["trace"]:
                        print(
                            "TRACE: THREAD {0} get work {1}".format(index, w))

                    if cond(w):
                        try:
                            ret = w.invoke(ops)
                        except Exception:
                            info.err = True
                            return
                        if ret is False:
                            info.err = True
                            return
                        if ret == 0:
                            info.sum += 1

                    for r in [self.core.get(t) for t in w.rdepends]:
                        r.rcounter = r.rcounter + 1
                        if r.rcounter == len(r.deps):
                            works.put(r)

                    info.have_done += 1

                    if core.runtime["trace"]:
                        print(
                            "TRACE: THREAD {0} finished with work {1}".format(
                                index, w)
                        )

                    continue
                lock.release()

        threads_list = [
            threading.Thread(target=thread_func, args=(i,)) for i in range(0, threads)
        ]

        for t in threads_list:
            t.start()

        for t in threads_list:
            t.join()

        if info.err:
            print(licant.util.red("runtime error (multithreads mode)"))
            exit(-1)
        return info.sum

    def reverse_recurse_invoke(self, *args, **kwargs):
        if "threads" in kwargs:
            if kwargs["threads"] == 1:
                return self.reverse_recurse_invoke_single(*args, **kwargs)
            else:
                return self.reverse_recurse_invoke_threads(*args, **kwargs)
        else:
            return self.reverse_recurse_invoke_single(*args, **kwargs)

    def __str__(self):
        ret = ""
        for d in sorted(self.depset):
            t = self.core.get(d)
            s = "{}: {}\n".format(d, sorted(t.deps))
            ret += s
        ret = ret[:-1]
        return ret


class Target:
    __actions__ = {"actlist", "print", "dependies"}

    def __init__(self, tgt, deps=[], action=lambda s: None, need_if=lambda s: True, weakdeps=[], actions=None, __help__=None, **kwargs):
        self.tgt = tgt
        deps = self.expand_globs(deps)
        self.deps = set(deps)
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

    def dependies(self):
        print(self.deps)

    def name(self):
        return self.tgt

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
        return [self.core.get(d) for d in self.deps]

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
                """
        if core.runtime["trace"]:
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
            # return licant.util.cutinvoke(func, *args, **kwargs)
            return func(*args, **kwargs)

        else:
            # return licant.util.cutinvoke(func, self, *args, **kwargs)
            return func(self, *args, **kwargs)

    def __repr__(self):
        """По умолчанию вывод Target на печать возвращает идентификатор цели"""
        return self.tgt


class UpdateStatus(Enum):
    Waiting = 0
    Keeped = 1
    Updated = 2


class UpdatableTarget(Target):
    __actions__ = Target.__actions__.union(
        {"recurse_update", "recurse_update_get_args", "update", "update_if_need"}
    )

    def __init__(
        self,
        tgt,
        deps,
        need_if=lambda s: False,
        default_action="recurse_update_get_args",
        update_status=UpdateStatus.Waiting,
        **kwargs
    ):
        Target.__init__(self, tgt, deps,
                        default_action=default_action, **kwargs)
        self.update_status = update_status
        self.need_if = need_if

    def recurse_update_get_args(self):
        return self.recurse_update(threads=core.runtime["threads"])

    def update(self, *args, **kwargs):
        licant.error("Unoverrided update method")

    def self_need(self):
        if self.need_if is not None:
            return self.need_if(self)
        return False

    def has_updated_depends(self):
        depends = self.get_deplist()

        for d in depends:
            if (
                not isinstance(d, UpdatableTarget)
                or d.update_status == UpdateStatus.Updated
            ):
                return True

            if d.update_status == UpdateStatus.Waiting:
                print(d)
                licant.error("Unwalked depends in UpdatableTarget")

        return False

    def invoke_function_or_method(self, act):
        if isinstance(act, types.MethodType):
            return act()
        else:
            return act(self)

    def update_if_need(self):
        if self.has_updated_depends() or self.self_need():  # self.invoke("self_need"):
            self.update_status = UpdateStatus.Updated
            # self.invoke("update")
            return self.invoke_function_or_method(self.update)
        else:
            self.update_status = UpdateStatus.Keeped
            return True

    def recurse_update(self, threads=1):
        stree = self.core.subtree(self.tgt)
        stree.reverse_recurse_invoke(
            ops="update_if_need", threads=threads)


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


def routine_decorator_do(func=None, deps=[], update_if=lambda s: False, tgt=None):
    core.add(Routine(func=func, deps=deps, update_if=update_if, tgt=tgt))
    return func


def routine_decorator(func=None, **kwargs):
    if inspect.isfunction(func):
        return routine_decorator_do(func, **kwargs)
    else:
        def decorator(func):
            return routine_decorator_do(func, **kwargs)
        return decorator


def print_targets_list(target, *args):
    if core.runtime["debug"]:
        print("print_targets_list args:{}".format(args))

    if len(core.targets) == 0:
        print("targets doesn't founded")
        return

    keys = sorted(core.targets.keys())

    if len(args) > 0:
        keys = [m for m in keys if re.search(args[0], m)]

    for k in keys:
        print(k)


def print_target_info(taget, *args):
    if len(args) == 0:
        licant.error("Need target mnemo")

    print("name:", core.get(args[0]))
    print("deps:", sorted(core.get(args[0]).deps))


def print_deps(taget, *args):
    if len(args) == 0:
        name = licant.cli.default_target
    else:
        name = args[0]

    lst = sorted(core.depends_as_set(name))
    for l in lst:
        print(l)


def print_subtree(target, tgt):
    print(core.subtree(tgt))


corediag_target = Target(
    tgt="corediag",
    deps=[],
    targets=print_targets_list,
    tgtinfo=print_target_info,
    subtree=print_subtree,
    printdeps=print_deps,
    actions={"targets", "tgtinfo", "subtree", "printdeps"},
    __help__="Core state info",
)

core.add(corediag_target)


def do(lst):
    core.get(lst[0]).invoke(lst[1], *lst[2:])


def get_target(name):
    return core.get(name)
