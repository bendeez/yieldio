from yieldio import EventLoop, Connection



loop = EventLoop(max_connections=100)

def task_4():
    result = yield from loop.gather(*[loop.add_connection(Connection.create_connection("https://www.google.com/")) for _ in range(10)])
    return result

def task_3():
    result = yield from task_4()
    return result
def task_2():
    result = yield from loop.gather(*[loop.add_connection(Connection.create_connection("https://github.com/")) for _ in range(10)])
    return result

def task_1():
    result = yield from loop.gather(loop.create_task(task_3()),loop.create_task(task_2()),loop.add_connection(Connection.create_connection("https://www.google.com/")))
    return result

def main():
    result = yield loop.create_task(task_1())
    print(result)

import time
start = time.time()
loop.run(main())
end = time.time()
print(end - start)