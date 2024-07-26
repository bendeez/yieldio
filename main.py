from yieldio import EventLoop, YieldClient



def task_4():
    result = yield from EventLoop.gather(*[YieldClient.request("https://www.google.com/") for _ in range(10)])
    return result

def task_3():
    result = yield from task_4()
    return result
def task_2():
    result = yield from EventLoop.gather(*[YieldClient.request("https://www.google.com/") for _ in range(10)])
    return result

def task_1():
    result = yield from EventLoop.gather(EventLoop.create_task(task_3()),EventLoop.create_task(task_2()),YieldClient.request("https://youtube.com"))
    return result

def main():
    result = yield EventLoop.create_task(task_1())
    print(result)


EventLoop.run(main())