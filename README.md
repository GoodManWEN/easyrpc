 # EASYRPC
 High availability rpc framework but easy to use.
 
 # Features
 - Both synchronize and asynchronize is allowed register to server.
 - Both synchronize and asynchronize call method is provided by the client.
 - High performance & low latency with async preforked module.
 - Distributed notice service supported by etcd.(Developing.
 - Some more black magics.
 
 # Installation
 

```
pip install git+https://github.com/NCNU-OpenSource/testrepo.git
```
> Currently continuous integration not activated , reliability might be limited.

 # Get started
 
 > Notification : since distributed support is still under development , only easy mode (no support from etcd) is allowed in current version.
 
 To get started , you may create a rpc server like this
 ```Python3
 # server.py
 from easyrpc import *
 import asyncio
 
 s = rpc_server(port = 25000)
 
 @s.register()
 def test(n):
     return n+1
 
 # standard startover with asyncio api , easy to control
 asyncio.run(s.start_serving())
 ```
 \* if you're using pypy or python version 3.6 ,you may need to pass eventloop explicitly like this:
 ```
 loop = asyncio.get_event_loop()
 loop.run_until_complete(s.start_serving(loop))
 ```
 
Then you may create a client file like this:<br>
which allows you to call whatever function you have registered in your server.
```Python3
# client.py
from easyrpc import *

c = rpc_client(port = 25000)

ret = c.test(1)
print(ret) ; assert ret == 2
```
# Usage
Quick view about advanced features:
- You can register both synchronize and asynchronize functions ,they will all behave asynchronizely as service.
- You can use prefork method to improve handling capacity.
- When register you can use `maximum_flow:int` to control overall flow capability of each function registered.
- `unstable_network:bool` helps you control if your server need to maintain a datastructure preventing repeated execute cause by network fluctuation , or just resend call when request failed , Which may reduce performance.
```Python3
# server.py
from easyrpc import *

s = rpc_server(port = 25000)

@s.register()
async def fib_async(n):
    a , b = 0 , 1
    for i in range(n):
        a , b = b , a + b
    return a

@s.register(maximum_flow = 100)
def fib_sync(n):
    if n<2:
        return n
    return fib(n-1) + fib(n-2)

s.prefork(bindcore = False)
asyncio.run(s.start_serving())
```
`bindcore:bool` binds each process to a cpu core specifily which helps reduce cache miss ,but limits the flexibility of kernel's tasks scheduling .Default False.

> Notification: since fork copy memory space as the same from parent to child process , where you fork matters . For example ,if you fork before register function ,then each function will have its own process lock. Fork *IS NOT* supported on windows.

- Both synchronize and asynchronize method is offered by client ,use `sync:bool` to control.
```Python3
# client_demo2.py
from easyrpc import *
import asyncio
import time

c = rpc_client(port = 25000)

# This function blocks until answer returns back
assert c.fib_async(1, sync = True) == None 

async def main():
    start_time = time.time()
    tasks = (c.fib_async(i) for i in range(1000))
    ret = await asyncio.gather(*tasks)   # you can make multiple \
                                         # requests at the same time. 
    print(f"Get {len(ret)} results ,for last three result  \
          shows {ret[-3:]} ,takes time {time.time()-start_time}s.")
asyncio.run(main())
```
- sync functions registered whill be running in process pool , since it takes a long communicating time(about 1ms) , make sure if you could get more time back when you call it. The following example shows that with this frame work you can take advantage of multi cores.
```Python3
# client_demo3.py
from easyrpc import *
from multiprocessing import cpu_count
import asyncio , time

c = rpc_client(port = 25000)

async def main():
    start_time_1 = time.time()
    ret1 = await c.fib_sync(30)
    end_time_1 = time.time()
    ret2 = await asyncio.gather((c.fib_sync(30) for i in range(cpu_count())))
    end_time_2 = time.time()
    assert ret2 == [ret1] * cpu_count()
    print(f"Single call takes time {end_time_1 - start_time}s while {cpu_count()} \
          times call takes {end_time_2 - end_time_1}s")
asyncio.run(main())
```

# Some more magic.
Pickle is a magic library python provides serialize service ,which is a stack describe language in essence. It maks it possible to share high level objects between process ,however it's low performance comparing to msgpack and not secure against erroneous maliciously constructed data.
Pickle protocol is defaultly disabled in easyrpc.
For flaxible use ,pickle can help us dealing with server's own data structure bu sending ape. 

```Python3
from easyrpc import *
import asyncio ,os

c = rpc_client(port = 25000)

func = lambda x ,y:(os.system('clear') ,print("This is a magic!") , x**2 + y)
assistant = c.magicwarp() # warp function to a magic assistant object
ret = c.magiccall(assistant)(11 , 10) # with help of assistant ,magic call returns a callable.
assert ret == [None , None , 131]
```
You will suprizingly relize that console of server.py has been changed.

# Performace

- RPS on different platform.
> Testing platform: <br>
>    CPU : Ryzen 1700x<br>
>    network interface : Intel(R) Dual Band Wireless-AC 3165<br>
>    VM 0kb local loopback<br>

![](https://github.com/NCNU-OpenSource/testrepo/blob/master/benchmarks.png?raw=true)

- Latency<br>

|-----|pypy3|uvloop|cpython
server|------|------|------|
client|cont1|cont2|cont3|
> seems like markdown tables not work here
