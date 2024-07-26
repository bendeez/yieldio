import selectors
from queue import Queue
from .task import Task
from .future import Future
import inspect


class EventLoop:
    running_loop = None

    def __init__(self, max_clients=100):
        EventLoop.running_loop = self
        self.select_clients = []
        self.select = selectors.DefaultSelector()
        self.max_clients = max_clients
        self.client_queue = Queue()

    def run_gen(self, main_gen):
        if inspect.isgenerator(main_gen):
            fut = next(main_gen)
            self.run_iteration_until_complete()
            try:
                while True:
                    fut = main_gen.send(fut.result)
                    self.run_iteration_until_complete()
            except StopIteration:
                pass

    def run_iteration_until_complete(self):
        """
        selector callbacks continue unblocking tasks
        :return:
        """
        while True:
            self.check_queue_clients()
            if len(self.select_clients) == 0:
                break
            events = self.select.select()
            for key, mask in events:
                client = key.data
                if mask & selectors.EVENT_READ:
                    client.read_callback(loop=self)
                if mask & selectors.EVENT_WRITE:
                    client.write_callback(loop=self)


    def check_queue_clients(self):
        """
            checks for waiting requests/connections when
            the max connection level isn't reach
            after a connection has been removed from
            select connections
        """
        if len(self.select_clients) < self.max_clients:
            if not self.client_queue.empty():
                client = self.client_queue.get()
                self.select_clients.append(client)
                self.select.register(client.sock, selectors.EVENT_READ | selectors.EVENT_WRITE,
                                     data=client)

    def add_client(self, client):
        """
            if the fut is not none, it means that when the
            connection initially was attempted to be registered
            to the selectors but there were too many connections
            so the connection was sent to the queue along with
            its future attribute being set
        :param client
        :return:
        """
        fut = Future()
        client.fut = fut
        if len(self.select_clients) < self.max_clients:
            self.select_clients.append(client)
            self.select.register(client.sock, selectors.EVENT_READ | selectors.EVENT_WRITE,
                                 data=client)
        else:
            # limits the amount of concurrent connections
            self.client_queue.put(client)
        return fut

    def remove_client(self, client):
        self.select_clients.remove(client)
        self.select.unregister(client.sock)

    def modify_event(self, client, method):
        if method == "r":
            event = selectors.EVENT_READ
        elif method == "w":
            event = selectors.EVENT_WRITE
        else:
            return
        self.select.modify(client.sock, event, data=client)

    @classmethod
    def run(cls, main_gen, max_clients=100):
        loop = cls(max_clients=max_clients)
        loop.run_gen(main_gen)

    @staticmethod
    def gather(*args):
        loop = EventLoop.running_loop
        if loop is not None:
            task = Task(loop=loop)
            yield from task.gather_tasks(*args)
            return task.result
        else:
            raise RuntimeError("No event loop is running")

    @staticmethod
    def create_task(gen):
        loop = EventLoop.running_loop
        if loop is not None:
            if inspect.isgenerator(gen):
                """
                any function that returns
                a future instance
                :param fut:
                :return: task
                """
                task = Task(loop, gen)
                task.start()
                return task
            else:
                raise Exception("Tasks can only wrap around generators")
        else:
            raise RuntimeError("No event loop is running")