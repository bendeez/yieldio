*Work in Progress!*

A custom made event loop with yield and yield from,
background tasks, and helper functions, along with concurrent synchronization.

The selectors module makes this all possible.

https://docs.python.org/3/library/selectors.html

![Screenshot 2024-06-21 125920](https://github.com/bendeez/async_event_loop/assets/127566471/378260f9-9145-49ff-b910-366f1204171f)

```python
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
