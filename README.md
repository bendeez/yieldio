*Work in Progress!*

A custom made event loop with yield and yield from,
background tasks, and helper functions, along with concurrent synchronization.

The selectors module makes this all possible.

https://docs.python.org/3/library/selectors.html

![Screenshot 2024-06-21 125920](https://github.com/bendeez/async_event_loop/assets/127566471/378260f9-9145-49ff-b910-366f1204171f)

```python
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
    print(result)


loop.run(main())
