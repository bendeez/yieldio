from yieldio import EventLoop, Connection



loop = EventLoop(max_connections=15)

def task_4():
    result = yield loop.gather(*[loop.add_connection(Connection.create_connection("https://www.google.com/")) for _ in range(10)])
    return result

def task_3():
    result = yield from task_4()
    return result
def task_2():
    result = yield loop.add_connection(Connection.create_connection("https://www.google.com/"))
    return result

def task_1():
    result = yield loop.gather(loop.create_task(task_3()),loop.create_task(task_2()),loop.add_connection(Connection.create_connection("https://www.google.com/")))
    return result

def main():
    result = yield loop.create_task(task_1())
    for r in result:
        print(r)


loop.run(main())