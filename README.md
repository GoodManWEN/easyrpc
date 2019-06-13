 # EASYRPC
 High availability rpc framework but easy to use.
 
 # Features
 - Both synchronize and asynchronize is allowed register to server.
 - Both synchronize and asynchronize call method is provided by the client.
 - High performance & low latency with async preforked module.
 - Distributed notice service supported by etcd.(Developing.
 - Some more black magics.
 
 
 # Get started
 
 > Notification : since distributed support is still under developing , only easy mode is allowed in current version.
 
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
 
Then you may create a client file like this:
which allows you to call whatever function you have registered in your server.
```Python3
# client.py
from easyrpc import *

c = rpc_client(port = 25000)

ret = c.test(1)
print(ret) ; assert ret == 2
```
# Useage
ongoing
