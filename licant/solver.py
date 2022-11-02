from concurrent.futures import thread
from threading import Thread
from queue import Queue
import queue
import threading
import sys
from licant.util import invert_depends_dictionary, red


class DependableTarget:
    def __init__(self, name, deps, what_to_do, args=[], kwargs={}):
        self.name = name
        self.deps = set(deps)
        self.what_to_do = what_to_do
        self.args = args
        self.kwargs = kwargs
        self._is_done = False

    def doit(self):
        result = self.what_to_do(*self.args, **self.kwargs)
        self._is_done = True
        return result

    def is_done(self):
        return self._is_done


class DependableTargetRuntime:
    def __init__(self, deptarget, task_invoker):
        self.deptarget = deptarget
        self.depcount = len(deptarget.deps)
        self.inverse_deps = set()
        self.task_invoker = task_invoker

    def is_done(self):
        return self.deptarget.is_done()

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
        result = self.deptarget.doit()
        with self.task_invoker.mtx:
            for dep in self.inverse_deps:
                dep.decrease_inverse_deps_count()
        return result

    def count_of_deps(self):
        return len(self.deptarget.deps)

    def name(self):
        return self.deptarget.name

    def __str__(self) -> str:
        return self.name()

    def __repr__(self) -> str:
        return self.name()


class TaskInvoker:
    def __init__(self, threads_count: int, trace=False):
        self.queue = Queue()
        self.threads_count = threads_count
        self.threads = []
        self.thread_on_base = [True] * threads_count
        self.done = False
        self.mtx = threading.Lock()
        self.trace = trace
        self.error_while_execution = False

    def start(self):
        if self.threads_count == 1:
            if self.trace:
                print("[Trace] single thread mode")
            self.single_worker()
            return

        if self.trace:
            print(f"[Trace] start with {self.threads_count} threads")

        for i in range(self.threads_count):
            t = Thread(target=self.worker, args=(i,))
            t.start()
            self.threads.append(t)

    def single_worker(self):
        while not self.queue.empty():
            task = self.queue.get()
            if self.trace:
                print(f"[Trace] do: {task.name()}")
            result = task.doit()
            if self.trace:
                print(f"[Trace] result of last task: ", result)
            if result is False:
                self.done = True
                self.error_while_execution = True
                print(
                    f"{red('LicantError')}: Error while executing task {task.name()}")
                break

    def worker(self, no):
        while not self.done:
            try:
                task = self.queue.get(timeout=0.4)
                with self.mtx:
                    self.thread_on_base[no] = False
                if self.trace:
                    print(f"[Trace] thread:{no} do task: {task.name()}")
                result = task.doit()

                if self.done:
                    break

                if self.trace:
                    print(f"[Trace] thread:{no} result of last task: ", result)
                if result is False:
                    self.done = True
                    self.error_while_execution = True
                    print(
                        f"{red('LicantError')}: Error while executing task {task.name()}")
                    break

                with self.mtx:
                    self.thread_on_base[no] = True
                    if all(self.thread_on_base) and self.queue.empty():
                        self.done = True
                        break
            except queue.Empty:
                if all(self.thread_on_base) and self.queue.empty():
                    self.done = True
                    break
            except KeyboardInterrupt:
                self.done = True
                self.error_while_execution = True
                break

    def add_target(self, target):
        self.queue.put(target)

    def stop(self, wait=True):
        self.done = True
        if wait:
            for t in self.threads:
                t.join()

    def wait(self):
        try:
            for t in self.threads:
                t.join()
        except KeyboardInterrupt:
            print(f"{red('LicantError')}: Execution was interrupted by user")
            self.done = True
            self.error_while_execution = True
            for t in self.threads:
                t.join()


class UnknowTargetError(Exception):
    pass


class NoOneNonDependableTarget(Exception):
    pass


class CircularDependencyError(Exception):
    def __init__(self, lst):
        self.lst = lst
        Exception.__init__(self, lst)


class DoubleDependsError(Exception):
    def __init__(self, dep):
        Exception.__init__(self, dep)


class ConnectivityError(Exception):
    def __init__(self, nonvisited):
        self.lst = nonvisited
        Exception.__init__(self, self.lst)


class InverseRecursiveSolver:
    def __init__(self, targets: list, count_of_threads: int = 1, trace: bool = False):
        self.trace = trace
        self.check(targets)
        self.double_depends_check(targets)
        self.task_invoker = TaskInvoker(count_of_threads, trace)

        self.deptargets = [DependableTargetRuntime(
            target, self.task_invoker) for target in targets]

        self.names_to_deptargets = {
            target.name(): target for target in self.deptargets}
        deps_of_targets = self.collect_depends_of_targets(self.deptargets,
                                                          self.names_to_deptargets)
        inverse_deps_of_targets = invert_depends_dictionary(deps_of_targets)

        assert len(inverse_deps_of_targets) == len(self.deptargets)

        for deptarget in self.deptargets:
            deptarget.set_inverse_deps(inverse_deps_of_targets[deptarget])

        non_dependable_targets = self.get_non_dependable_targets()
        for target in non_dependable_targets:
            self.task_invoker.add_target(target)

        if len(non_dependable_targets) == 0:
            raise NoOneNonDependableTarget()

        self.connectivity_check(self.deptargets, non_dependable_targets)

    def double_depends_check(self, targets):
        for target in targets:
            for dep in target.deps:
                count = 0
                for dep2 in target.deps:
                    if dep == dep2:
                        count += 1
                if count > 1:
                    raise DoubleDependsError(dep)

    def dfs(self, target, visited, path):
        visited.add(target)
        path.append(target)
        for dep in target.inverse_deps:
            if dep in path:
                raise CircularDependencyError(path + [dep])
            if dep not in visited:
                self.dfs(dep, visited, path)
        path.pop()

    def connectivity_check(self, deptargets, non_dependable_targets):
        visited = set()
        path = []
        for target in non_dependable_targets:
            self.dfs(target, visited, path)

        if len(visited) != len(deptargets):
            nonvisited = set(deptargets) - visited
            raise ConnectivityError(nonvisited)

    def collect_depends_of_targets(self, deptargets, names_to_deptargets):
        try:
            deps_of_targets = {}
            for deptarget in deptargets:
                deps_of_targets[deptarget] = set()
                for dep in deptarget.deps():
                    deps_of_targets[deptarget].add(names_to_deptargets[dep])
            return deps_of_targets
        except KeyError as e:
            raise UnknowTargetError(e)

    def check(self, targets):
        for target in targets:
            if not isinstance(target, DependableTarget):
                raise TypeError(
                    "Target must be DependableTarget, but:", target.__class__)
            for dep in target.deps:
                if not isinstance(dep, str):
                    raise TypeError("Dep must be str")

    def get_non_dependable_targets(self):
        return [target for target in self.deptargets if target.count_of_deps() == 0]

    def exec(self):
        self.task_invoker.start()
        self.task_invoker.wait()
        if not self.task_invoker.error_while_execution:
            assert self.task_invoker.queue.empty()
            assert all(d.depcount == 0 for d in self.deptargets)
            assert all(d.is_done() for d in self.deptargets)
        if self.trace:
            print("[Trace] Execution finished. Status:",
                  not self.task_invoker.error_while_execution)
        return not self.task_invoker.error_while_execution
