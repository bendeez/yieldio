from .future import Future
import inspect

class Task(Future):

    def __init__(self, loop, called_function=None):
        super().__init__()
        self.loop = loop
        """
            some tasks run functions that return
            future or group of futures or generators 
            and some tasks gather tasks
        """
        self.main_called_function = called_function
        self.finished_iteration = False
        self.returned_futures = []
        self.unfinished_futures = [] # keep track of unfinished futures to avoid unfinished results

    def gather_tasks(self,*tasks):
        """
            gather connections and tasks
            This task could be inside another task
        """
        responses = []
        for task in tasks:
            if inspect.isgenerator(task):
                response = yield from task # yield from generator (task)
            else:
                response = yield task
            responses.append(response)
        self.set_result(responses)

    def start(self):
        """
            runs task without blocking
            selector callbacks will resume task
        """
        if self.main_called_function:
            if self.finished_iteration:
                """
                    means an iteration has finished
                """
                self.set_main_task_iteration_value()
            else:
                """
                    means start of main task
                """
                if inspect.isgenerator(self.main_called_function):
                    iter = next(self.main_called_function)
                    self.run_main_generator_task(iter)
                elif isinstance(self.main_called_function, Future):
                    self.run_main_non_generator_task()

    def set_main_task_iteration_value(self):
        try:
            if isinstance(self.returned_futures, list):
                result = [fut.result for fut in self.returned_futures]
            else:
                result = self.returned_futures.result  # single future was returned
            iter = self.main_called_function.send(result)  # returned from child gen
            self.finished_iteration = False  # set it to false for next generator iteration
            if inspect.isgenerator(iter):
                self.run_child_gen(iter)
            else:
                self.run_main_generator_task(iter)
        except StopIteration as e:
            """
                The task values that are being set
                could be tasks inside a gather generator
                or the main task.
            """
            self.set_result(e.value)

    def run_main_generator_task(self,iter):
        try:
            if inspect.isgenerator(iter):
                self.run_child_gen(iter)
            elif isinstance(iter, Future):
                fut = iter
                fut.unblocking_task = self
                self.returned_futures = fut
                self.unfinished_futures.append(fut)
                self.finished_iteration = True
        except StopIteration as e:
            if isinstance(e.value, (Future, Task)):
                self.returned_futures = e.value.result
            self.finished_iteration = True

    def run_main_non_generator_task(self):
        fut = self.main_called_function
        if self.main_finished_iteration:
            self.set_result(fut.result)
        else:
            fut.unblocking_task = self
            self.unfinished_futures.append(fut)
            self.main_finished_iteration = True
            """
                selector callback will resume this task
            """

    def run_child_gen(self,gen):
        try:
            iter = next(gen)
            while True:
                fut = gen.send(iter)
                if inspect.isgenerator(fut):
                    self.run_child_gen(fut)
                elif isinstance(fut,Future):
                    """
                        tasks can also be futures because they inherit from it
                    """
                    fut.unblocking_task = self
                    self.unfinished_futures.append(fut)
        except StopIteration as e:
            """
                the task is a task inside this unblocking task
                task value was set because it's the end of the generator
            """
            self.returned_futures = e.value.result # task result are futures that will be set later
            self.finished_iteration = True

    def update_progress(self,fut):
        """
            selector result callbacks will continue the task
        :param fut:
        :param result:
        :return:
        """
        self.unfinished_futures.remove(fut)
        if len(self.unfinished_futures) == 0:
            self.start() # continue task after previous future is set