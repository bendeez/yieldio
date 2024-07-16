from .future import Future
from .connection import Connection
import inspect

class Task(Future):

    fut_reference = [] # used to synchronize tasks in between print statements

    def __init__(self, loop, called_function=None):
        super().__init__()
        self.loop = loop
        """
            some tasks run functions that return
            future or group of futures or generators 
            and some tasks gather tasks
        """
        self.main_called_function = called_function
        self.called_function = called_function
        self.called_function_finished = False
        self.returned_futures = []
        self.results = []
        self.unfinished_futures = [] # keep track of unfinished futures to avoid unfinished results

    def gather_tasks(self,*tasks):
        """
            gather connections and tasks
            This task could be inside another task
        """
        futures = []
        for task in tasks:
            if isinstance(task,Task):
                futures.append(task)
            elif isinstance(task,Connection):
                fut = self.loop.add_connection(task, in_gather=True)
                futures.append(fut)
        if isinstance(tasks[-1],Task):
            Task.fut_reference.append(tasks[-1])
        elif isinstance(tasks[-1],Connection):
            Task.fut_reference.append(tasks[-1].fut)
        responses = []
        for fut in futures:
            response = yield fut
            responses.append(response)
        self.set_result(responses)

    def start(self):
        """
            runs task without blocking
        """
        if self.main_called_function:
            if self.called_function_finished: # for child gen if one was running (means main gen has already ran)
                try:
                    iter = self.main_called_function.send([fut.result for fut in self.returned_futures]) # returned from child gen
                    self.called_function_finished = False  # set it to false for next generator
                    if inspect.isgenerator(iter):
                        self.run_child_gen(iter)
                except StopIteration as e:
                    self.set_result(e.value)
            else:
                if inspect.isgenerator(self.main_called_function):
                    try:
                        gen = self.main_called_function
                        iter = next(gen)
                        if inspect.isgenerator(iter):
                            self.called_function = iter
                            self.run_child_gen(iter)
                        else:
                            while True:
                                fut = gen.send(iter)
                                fut.unblocking_task = self
                                self.unfinished_futures.append(fut)
                    except StopIteration as e:
                        self.returned_futures = e.value.result
                        self.called_function_finished = True
                elif isinstance(self.main_called_function,Future):
                    fut = self.main_called_function
                    if self.main_called_function_finished:
                        self.set_result(fut.result)
                    else:
                        fut.unblocking_task = self
                        self.unfinished_futures.append(fut)
                        self.main_called_function_finished = True

    def run_child_gen(self,gen):
        try:
            iter = next(gen)
            while True:
                fut = gen.send(iter)
                fut.unblocking_task = self
                self.unfinished_futures.append(fut)
        except StopIteration as e:
            """
                the task is a task inside this unblocking task
            """
            task = e.value # task value was set because it's the end of the generator
            self.returned_futures = task.result # task result are futures that will be set later
            self.called_function_finished = True

    def update_progress(self,fut,result):
        """
            selector result callbacks will continue the task
        :param fut:
        :param result:
        :return:
        """
        self.unfinished_futures.remove(fut)
        if len(self.unfinished_futures) == 0:
            self.start() # continue task after previous future is set


    def set_unblocking_task_result(self,values):
        if isinstance(values, list):
            if all(isinstance(value, Future) for value in values):
                for fut in values:
                    if isinstance(fut, Future):
                        self.results.append(self.fut_result[fut])
                    else:
                        self.results.append(fut)  # fut already has a value
                self.set_result(self.results)
            else:
                self.set_result(values)
        else:
            self.set_result(values)