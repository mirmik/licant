from concurrent.futures import thread
from threading import Thread
from queue import Queue
import queue
import threading
import sys
from licant.util import invert_depends_dictionary


class DependableTarget:
    def __init__(self, name, deps, what_to_do, args=[], kwargs={}):
        self.name = name
        self.deps = deps
        self.what_to_do = what_to_do
        self.args = args
        self.kwargs = kwargs

    def doit(self):
        self.what_to_do(*self.args, **self.kwargs)


class DependableTargetRuntime:
    def __init__(self, deptarget, task_invoker):
        self.deptarget = deptarget
        self.depcount = len(deptarget.deps)
        self.inverse_deps = set()
        self.task_invoker = task_invoker

    def set_inverse_deps(self, inverse_deps: set):
        self.inverse_deps = inverse_deps

    def deps(self):
        return self.deptarget.deps

    def decrease_inverse_deps_count(self):
        self.depcount -= 1
        if self.depcount == 0:
            self.task_invoker.add_target(self)
        assert self.depcount >= 0

    def doit(self):
        self.deptarget.doit()
        with self.task_invoker.mtx:
            for dep in self.inverse_deps:
                dep.decrease_inverse_deps_count()

    def count_of_deps(self):
        return len(self.deptarget.deps)

    def name(self):
        return self.deptarget.name

    def __str__(self) -> str:
        return self.name()

    def __repr__(self) -> str:
        return self.name()


class TaskInvoker:
    def __init__(self, threads_count, total_tasks_count):
        self.queue = Queue()
        self.threads_count = threads_count
        self.threads = []
        self.done = False
        self.total_tasks_count = total_tasks_count
        self.mtx = threading.Lock()

    def start(self):
        for i in range(self.threads_count):
            t = Thread(target=self.worker)
            t.start()
            self.threads.append(t)

    def worker(self):
        while not self.done:
            try:
                task = self.queue.get(timeout=0.4)
                task.doit()

                with self.mtx:
                    self.total_tasks_count -= 1
                    if self.total_tasks_count == 0:
                        self.done = True
                        break
            except queue.Empty:
                pass

    def add_target(self, target):
        self.queue.put(target)

    def stop(self, wait=True):
        self.done = True
        if wait:
            for t in self.threads:
                t.join()

    def wait(self):
        for t in self.threads:
            t.join()


class InverseRecursiveSolver:
    def __init__(self, targets: list, count_of_threads=1):
        self.check(targets)
        self.task_invoker = TaskInvoker(count_of_threads, len(targets))
        self.deptargets = [DependableTargetRuntime(target, self.task_invoker) for target in targets]

        self.names_to_deptargets = {target.name(): target for target in self.deptargets}
        deps_of_targets = self.collect_depends_of_targets(self.deptargets,
                                                          self.names_to_deptargets)
        inverse_deps_of_targets = invert_depends_dictionary(deps_of_targets)
        for deptarget in self.deptargets:
            deptarget.set_inverse_deps(inverse_deps_of_targets[deptarget])

        non_dependable_targets = self.get_non_dependable_targets()
        for target in non_dependable_targets:
            self.task_invoker.add_target(target)

    def collect_depends_of_targets(self, deptargets, names_to_deptargets):
        deps_of_targets = {}
        for deptarget in deptargets:
            deps_of_targets[deptarget] = set()
            for dep in deptarget.deps():
                deps_of_targets[deptarget].add(names_to_deptargets[dep])
        return deps_of_targets

    def check(self, targets):
        for target in targets:
            if not isinstance(target, DependableTarget):
                raise TypeError("Target must be DependableTarget, but:", target.__class__)
            for dep in target.deps:
                if not isinstance(dep, str):
                    raise TypeError("Dep must be str")

    def get_non_dependable_targets(self):
        return [target for target in self.deptargets if target.count_of_deps() == 0]

    def exec(self):
        self.task_invoker.start()
        self.task_invoker.wait()
