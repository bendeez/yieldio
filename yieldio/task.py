from .future import Future

class Task(Future):

    def __init__(self, loop, gen=None):
        super().__init__()
        self.loop = loop
        self.gen = gen

    def gather_tasks(self,*tasks):
        """
            gather generators and futures
            This task could be inside another task
        """
        responses = []
        for task in tasks:
            response = yield task
            responses.append(response)
        self.set_result(responses)

    def start(self):
        """
            runs task without blocking
            selector callbacks will resume task
        """
        fut = next(self.gen)
        fut.add_done_callback(self.unpause,fut)

    def unpause(self, prev_fut):
        try:
            fut = self.gen.send(prev_fut.result)
            if fut.finished:
                self.unpause(fut)
            else:
                fut.add_done_callback(self.unpause,fut)
        except StopIteration as e:
            self.set_result(e.value)