import selectors
from queue import Queue
from .task import Task
from .future import Future
import inspect


class EventLoop:

    def __init__(self, max_connections=100):
        self.select_connections = []
        self.select = selectors.DefaultSelector()
        self.max_connections = max_connections
        self.connection_queue = Queue()

    def run(self, main_gen):
        # main gen
        iter = next(main_gen) # start the generator and returns first yield
        self.run_main_gen(main_gen,iter)

    def run_main_gen(self,main_gen,iter):
        if inspect.isgenerator(main_gen):
            try:
                while True:
                    """ 
                        returning iter 
                        overrides previous iter with updated generator iter for the next
                        iteration of the while loop
                    """
                    if inspect.isgenerator(iter):
                        iter = self.run_child_gen(iter, main_gen)
                    elif isinstance(iter,Task): # unblocking task
                        iter = self.run_iteration_until_complete(main_gen,iter)
                    elif isinstance(iter,Future):
                        iter = self.run_iteration_until_complete(main_gen,iter)
            except StopIteration:
                pass

    def run_child_gen(self, child_gen, main_gen):
        try:
            child_gen_iter = next(child_gen) # adds all connection sockets to selectors to start the requests
            while True:
                child_gen_iter = self.run_iteration_until_complete(child_gen,child_gen_iter)
        except StopIteration as e:
            task = e.value
            iter = main_gen.send(task.result) # returns next iteration of the main generator
            return iter

    def run_iteration_until_complete(self, gen, fut):
        """
        selector callbacks continue unblocking tasks
        :param gen:
        :param fut:
        :return:
        """
        # main gen
        while True:
            try:
                if len(self.select_connections) == 0:
                    self.check_queue_connections()
                if fut.finished:
                    iter = gen.send(fut.result)
                    return iter
                events = self.select.select()
                for key, mask in events:
                    connection = key.data
                    if mask & selectors.EVENT_READ:
                        connection.read_callback(loop=self)
                    if mask & selectors.EVENT_WRITE:
                        connection.write_callback(loop=self)
            except OSError:
                """
                    socket could already be unregistered because
                    it could finish before the unblocking task is ready
                    to check if the socket has received data due to the
                    task's nonblocking functionality
                """
                if isinstance(fut,Task):
                    fut.start()


    def check_queue_connections(self):
        """
            checks for waiting requests/connections when
            the max connection level isn't reach
            after a connection has been removed from
            select connections
        """
        if len(self.select_connections) < self.max_connections:
            if not self.connection_queue.empty():
                connection = self.connection_queue.get()
                if connection.fut:
                    self.add_connection(connection,connection.fut)
                else:
                    self.add_connection(connection)

    def gather(self, *args):
        task = Task(loop=self)
        yield from task.gather_tasks(*args)
        return task

    def create_task(self, called_function):
        """
        any function that returns
        a future instance
        :param fut:
        :return: task
        """
        task = Task(self, called_function)
        task.start()
        return task

    def add_connection(self, connection, fut=None,in_gather=False):
        """
            in gather=False makes it so we know to set the
            task's fut reference to synchronize the task
            in between print statements

            in_gather=True means that the setting
            the task's fut reference will be set
            in the task's gather function because only
            the last future/connection of the gather function
            needs to be set to the task's fut reference
        """
        if fut is None:
            fut = Future()
            connection.fut = fut
        if not in_gather:
            Task.fut_reference.append(fut)
        connection.connection_callback()
        if len(self.select_connections) < self.max_connections:
            self.select_connections.append(connection)
            self.select.register(connection.client, selectors.EVENT_READ | selectors.EVENT_WRITE,
                                 data=connection)
        else:
            # limits the amount of concurrent connections
            self.connection_queue.put(connection)
        return fut

    def remove_connection(self, connection):
        self.select_connections.remove(connection)
        self.select.unregister(connection.client)

    def modify_event(self, connection, method):
        if method == "r":
            event = selectors.EVENT_READ
        elif method == "w":
            event = selectors.EVENT_WRITE
        else:
            return
        self.select.modify(connection.client, event, data=connection)
