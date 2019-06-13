import asyncio
import inspect
import socket
from threading import Thread
from random import randint
from bisect import bisect_right
from time import time


from .server import rpc_base
from .selector import msgpack_selector
from .aside import timeouts
from .exceptions import *

RECV_TIMEOUT = 15
MAX_REQUEST_TOKEN = 2_0000_0000

def weight_choice(targ_list , weight_list):
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
            self._instantiation = False

            # init connect
            self._connectpool = {}
            sock = self.__class__.create_socket('',0,False)
            sock.connect(('',self._tempport))
            sock.setblocking(0)
            # self._connectpool['news'] = [[sock,sock,sock],[1024,1024,1024]]
            self._connectpool['current'] = [[sock,sock,sock],[1024,1024,1024]]

    def _sync_call(self , funcname , args , kwargs):

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

    async def _async_call(self , funcname , args , kwargs):

        if not self._instantiation:
            raise InstantiationError("You must create a task for client.instance() before you make a async call")

        current_request_token = self._request_token
        self._request_token = (self._request_token + 1) % MAX_REQUEST_TOKEN

        sdata = self._selector[0].encode(1,current_request_token ,funcname , args , kwargs)
        selected_server = weight_choice(*self._connectpool['current'])
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

    def _warpback(self, sc , data):
        if sc == 2:
            return data
        elif sc == 3:
            raise Exception(data)
        else:
            raise DecodingError("Some error occured reciveing message. It may caused by network outage ,or decoding invalid data.")

    async def instance(self , loop = None):
        # for every client:
        if loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except Exception as err:
                raise err
        else:
            self._loop = loop

        server = self._connectpool['current'][0][0]
        self._instantiation = True
        while True:        
            data , protocol = await self.protocoled_fetch(server)
            if not data:
                continue
            type_code , *args = self._selector[protocol].decode(data)
            if type_code:
                self._waiting_list[args[0]].set_result((type_code , args[1]))

    def __getattr__(self , name):

        def decorator(*args , **kwargs):
            if ('sync',True) in kwargs.items():
                del kwargs['sync']
                return self._sync_call(name , args , kwargs)
            else:
                return self._async_call(name , args , kwargs)

        return decorator