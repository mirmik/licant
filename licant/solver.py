import asyncio
from licant.util import invert_depends_dictionary, red
import contextlib


class DependableTarget:
    def __init__(self, name, deps, what_to_do, args=None, kwargs=None):
        self.name = name
        # множество имён зависимостей
        self.deps = set(deps)
        self.what_to_do = what_to_do
        # нормальные дефолты (без разделяемых списков/словарей)
        self.args = [] if args is None else args
        self.kwargs = {} if kwargs is None else kwargs
        self._is_done = False

    def doit_impl(self):
        result = self.what_to_do(*self.args, **self.kwargs)
        return result

    async def doit(self):
        # выносим в отдельный поток, чтобы не блокировать event loop
        result = await asyncio.to_thread(self.doit_impl)
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

    async def decrease_inverse_deps_count(self):
        self.depcount -= 1
        if self.depcount == 0:
            await self.task_invoker.add_target(self)
        assert self.depcount >= 0

    async def doit(self):
        result = await self.deptarget.doit()
        # после выполнения оповещаем всех, кто от нас зависит
        async with self.task_invoker.mtx:
            for dep in self.inverse_deps:
                await dep.decrease_inverse_deps_count()
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
    def __init__(self, threads_count: int, trace: bool = False):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.threads_count = threads_count
        self.tasks = []
        self.mtx = asyncio.Lock()
        self.trace = trace
        self.error_while_execution = False
        self.last_exception = None

    def run_until_complete(self, initial_targets):
        try:
            async def main():
                # кладём начальные задачи (без зависимостей) в очередь
                for t in initial_targets:
                    await self.add_target(t)
                await self.start()

            self.loop.run_until_complete(main())
        except KeyboardInterrupt:
            self.error_while_execution = True
            # аккуратно гасим все таски event loop’а
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                self.loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
        finally:
            with contextlib.suppress(RuntimeError):
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def start(self):
        if self.trace:
            print(f"[Trace] start with {self.threads_count} threads")

        for i in range(self.threads_count):
            task = asyncio.create_task(
                self.worker(f"worker-{i}", self.queue, i)
            )
            self.tasks.append(task)

        # ждём, пока все задачи в очереди будут отмечены как выполненные
        await self.queue.join()

        # после этого останавливаем воркеры
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def worker(self, name, queue, no):
        while True:
            try:
                target = await queue.get()
            except asyncio.CancelledError:
                break

            try:
                if self.error_while_execution:
                    # уже была ошибка — эту задачу не выполняем,
                    # но должны пометить как завершённую
                    if self.trace:
                        print(f"[Trace] {name}: skip task {target.name()} due to error flag")
                    continue

                if self.trace:
                    print(f"[Trace] thread:{no} do task: {target.name()}")

                result = await target.doit()

                if self.trace:
                    print(f"[Trace] thread:{no} result of last task: {result}")

                if result is False:
                    self.error_while_execution = True
                    print(f"{red('LicantError')}: Error while executing task {target.name()}")
            except Exception as e:
                # ловим любые падения задачи, чтобы не повесить queue.join()
                self.error_while_execution = True
                self.last_exception = e
                print(f"{red('LicantError')}: Exception while executing task {target.name()}: {e}")
            finally:
                # ВАЖНО: всегда вызываем task_done для взятой задачи
                queue.task_done()

    async def add_target(self, target):
        await self.queue.put(target)


class UnknowTargetError(Exception):
    pass


class NoOneNonDependableTarget(Exception):
    pass


class CircularDependencyError(Exception):
    def __init__(self, lst):
        self.lst = lst
        Exception.__init__(self, lst)


class ConnectivityError(Exception):
    def __init__(self, nonvisited):
        self.lst = nonvisited
        Exception.__init__(self, self.lst)


class InverseRecursiveSolver:
    def __init__(self, targets: list, count_of_threads: int = 1, trace: bool = False):
        self.trace = trace
        self.check(targets)

        self.task_invoker = TaskInvoker(count_of_threads, trace)

        # оборачиваем DependableTarget в runtime-объекты
        self.deptargets = [
            DependableTargetRuntime(target, self.task_invoker) for target in targets
        ]

        self.names_to_deptargets = {target.name(): target for target in self.deptargets}
        deps_of_targets = self.collect_depends_of_targets(
            self.deptargets, self.names_to_deptargets
        )
        inverse_deps_of_targets = invert_depends_dictionary(deps_of_targets)

        assert len(inverse_deps_of_targets) == len(self.deptargets)

        for deptarget in self.deptargets:
            deptarget.set_inverse_deps(inverse_deps_of_targets[deptarget])

        non_dependable_targets = self.get_non_dependable_targets()
        if len(non_dependable_targets) == 0:
            # нет ни одной вершины без зависимостей — значит цикл
            raise NoOneNonDependableTarget()

        self.connectivity_check(self.deptargets, non_dependable_targets)
        self.initial_targets = non_dependable_targets

    def check(self, targets):
        for target in targets:
            if not isinstance(target, DependableTarget):
                raise TypeError(
                    "Target must be DependableTarget, but: {}".format(
                        target.__class__
                    )
                )
            for dep in target.deps:
                if not isinstance(dep, str):
                    raise TypeError("Dep must be str")

    def dfs(self, target, visited, path):
        visited.add(target)
        path.append(target)
        for dep in target.inverse_deps:
            if dep in path:
                # нашли цикл
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
            # в графе есть зависимость на неизвестную цель
            raise UnknowTargetError(e)

    def get_non_dependable_targets(self):
        return [target for target in self.deptargets if target.count_of_deps() == 0]

    def exec(self):
        self.task_invoker.run_until_complete(self.initial_targets)

        if self.trace:
            print(
                "[Trace] Execution finished. Status:",
                not self.task_invoker.error_while_execution,
            )

        if self.task_invoker.error_while_execution:
            # если хотим более жёсткое поведение — тут можно пробрасывать last_exception
            return False

        # sanity-check’и
        assert self.task_invoker.queue.empty()
        assert all(d.depcount == 0 for d in self.deptargets)
        assert all(d.is_done() for d in self.deptargets)

        return True
