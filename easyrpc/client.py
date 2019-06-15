import asyncio
import inspect
import socket
import sys
from threading import Thread
from random import randint ,seed
from bisect import bisect_right
from time import time
from functools import partial


from .server import rpc_base
from .selector import msgpack_selector
from .aside import timeouts,autocheck
from .blackmagic import MagicianAssistant ,magicwarp , magiccall
from .exceptions import *

PY_37UP = sys.version_info >= (3, 7)
RECV_TIMEOUT = 15
MAX_REQUEST_TOKEN = 2_0000_0000

@asyncio.coroutine
def poptostackend():
    yield

def weight_choice(targ_list:list , weight_list:list) -> 'componient of targlist':
    weight_sum = []
    sum_ = 0
    for a in weight_list:
        sum_ += a
        weight_sum.append(sum_)
    t = randint(0, sum_ - 1)
    return targ_list[bisect_right(weight_sum, t)]

class rpc_client(rpc_base):
    """docstring for rpc_client"""
    def __init__(self , port = None,target_function = None,easymode = True):
        super(rpc_client, self).__init__()
 
        if easymode:
            if port == None:
                port = 25000
            self._tempport = port
            self._sock = self.__class__.create_socket('',0,False)
            self._selector = []
            self._selector.append(msgpack_selector())
            self._request_token = (randint(1,MAX_REQUEST_TOKEN) + int(time())) % MAX_REQUEST_TOKEN
            self._waiting_list = {}
            self.magicwarp = magicwarp
            self.magiccall = partial(magiccall,self)
            self._loopseted = False


            # init connect
            self._connectpool = {}
            sock = self.__class__.create_socket('',0,False)
            sock.connect(('',self._tempport))
            sock.setblocking(0)
            # self._connectpool['news'] = [[sock,sock,sock],[1024,1024,1024]]
            self._connectpool['current'] = [
                                                [   [sock,None],
                                                    [sock,None],
                                                    [sock,None]  
                                                ],
                                                [   1024,
                                                    1024,
                                                    1024    
                                                ]
                                            ]

    def _sync_call(self , funcname:str , args:tuple , kwargs:dict):

        sock = self.__class__.create_socket('',0,False)

        sock.connect(('',self._tempport))
        sdata = self._selector[0].encode(1,self._request_token ,funcname , args , kwargs)
        self._request_token += 1
        sock.sendall(sdata)

        data_header = sock.recv(4)

        if len(data_header)<4:return

        data_length = (data_header[0] << 16) + \
                  (data_header[1] << 8) + data_header[2]
        protocol = data_header[3] 

        if protocol > 2:return

        rdata = b''
        while len(rdata) < data_length:
            rdata += sock.recv(data_length - len(rdata))
        rdata = self._selector[0].decode(rdata)
        return self._warpback(rdata[0] ,rdata[2])

    async def _async_call(self , funcname:str , args:tuple , kwargs:dict):

        if not self._loopseted:
            if PY_37UP:
                self._loop = asyncio.get_running_loop()
            else:
                raise EventLoopError("If you are using python3.6 ,you should use client.set_event_loop(loop) to explicitly pass on EventLoop") 

        current_request_token = self._request_token
        self._request_token = (self._request_token + 1) % MAX_REQUEST_TOKEN

        sdata = self._selector[0].encode(1,current_request_token ,funcname , args , kwargs)

        selected_server = weight_choice(*self._connectpool['current'])
        
        if not selected_server[1]:

            if selected_server[1] is None:
                # preventing there's more other same-socket tasks in loop
                selected_server[1] = False 
                self._loop.create_task(self._instance(selected_server))
            # then ,go through if listening started
            # it takes about 300miniseconds to connect to a local server.
            loopcount = 0
            while not selected_server[1]:
                await asyncio.sleep(0.0004)
                await poptostackend()
                loopcount += 1
                if loopcount >= 100:
                    raise ConnectingError('Could not make connect to server')
        selected_server = selected_server[0]

        await self._loop.sock_sendall(selected_server , sdata)

        fut = self._loop.create_future()
        self._waiting_list[current_request_token] = fut
        try:
            with timeouts(RECV_TIMEOUT):
                res = await fut
        except Exception as err:
            fut.cancel()
            res = (3 , repr(err))
        return self._warpback(*res)


    def _warpback(self, sc:int , data:any):
        if sc == 2:
            return data
        elif sc == 3:
            raise Exception(data)
        else:
            raise DecodingError("Some error occured reciveing message. It may caused by network outage ,or decoding invalid data.")

    async def _instance(self , server_struct:list):
        server = server_struct[0]
        while True:
            server_struct[1] = True
            data , protocol = await self.protocoled_fetch(server)
            if not data:
                continue
            type_code , *args = self._selector[protocol].decode(data)
            if type_code:
                try:
                    self._waiting_list[args[0]].set_result((type_code , args[1]))
                except:
                    apss

    @autocheck
    def set_event_loop(self , loop):
        self._loop = loop
        self._loopseted = True

    def sync_call(self , name ,*args , **kwargs):
        return self._sync_call(name , args , kwargs)

    async def async_call(self , name , *args , **kwargs):
        return await self._async_call(name , args , kwargs)

    def __getattr__(self , name):

        def decorator(*args , **kwargs):
            if ('sync',True) in kwargs.items():
                del kwargs['sync']
                return self._sync_call(name , args , kwargs)
            else:
                return self._async_call(name , args , kwargs)

        return decorator
