


class Future:
    def __init__(self):
        self.result = None
        self.finished = False
        self.unblocking_task = None

    def set_result(self, result):
        self.result = result
        self.finished = True



