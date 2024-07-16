from AsyncLoop import EventLoop
from AsyncLoop import Connection



loop = EventLoop(max_connections=15)

# async def scrape_other_website():
#     results = await loop.gather(Connection.create_connection("https://www.google.com/"))
#     return results
#
# async def scrape_website(url):
#     first_result = await scrape_other_website()
#     print(first_result)
#     second_result = await
#     return second_result
#
# async def main(loop):
#     url = "https://github.com/"
#     task_1 = loop.create_task(scrape_website(url))
#     result = await loop.gather(task_1)
#     print(result)

# def hi():
#     url = "https://github.com/"
#     result = yield loop.gather(*[Connection.create_connection(url) for _ in range(10)])
#     print(result)
#     result = yield loop.gather(*[Connection.create_connection(url) for _ in range(10)])
#     print(result)
#     result = yield loop.add_connection(Connection.create_connection("https://www.google.com/"))
#     print(result)

def task_1(url):
    result_1 = yield loop.gather(*[Connection.create_connection("https://www.google.com/") for _ in range(10)])
    result = yield loop.gather(*[Connection.create_connection(url) for _ in range(10)])
    return result_1
def main():
    url = "https://github.com/"
    result = yield loop.create_task(task_1(url))
    print(result)
    result = yield loop.add_connection(Connection.create_connection("https://www.google.com/"))
    print(result)

loop.run(main())