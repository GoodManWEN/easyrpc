# from .timeoutbase import timeouts
# from .aside import autocheck
import asyncio
import socket
import os
import sys
import pickle
from multiprocessing import RLock , Value, cpu_count
from inspect import iscoroutinefunction
from concurrent.futures import ProcessPoolExecutor as Pool

from .aside import autocheck ,timeouts
from .selector import msgpack_selector , pickle_selector
from .exceptions import *

PY_37UP = sys.version_info >= (3, 7)
REQUEST_TIMEOUT = 9999 # 92
FOLLOWING_MESSAGE_TIMEOUT = 2
VARIFY_WORD = '`$$'
BUFFER_TIMEOUT_SECONDS = 3 # 10
SOCK_LISTEN_NUMBER = 100

class rpc_base(object):
    """docstring for rpc_base"""

    def create_socket(host:str , port:int , server:bool) -> socket.socket:
        sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET , socket.SO_REUSEADDR , 1)
        if server:
            sock.bind((host , port))
            sock.listen(SOCK_LISTEN_NUMBER)
            sock.setblocking(0) 
        return sock

    def __init__(self):
        super(rpc_base, self).__init__()
        self._selector = [msgpack_selector()]
    
    async def protocoled_fetch(self , client:socket.socket) -> tuple:

        # return None means close connection
        # return False means broken package

        try:
            async with timeouts(REQUEST_TIMEOUT):
                data_header = await self._loop.sock_recv(client, 4)
        except (ConnectionResetError ,asyncio.TimeoutError): 
            client.close(); return None ,None

        if not data_header: return None , None
        elif len(data_header) < 4: return False ,None

        data_length = (data_header[0] << 16) + \
                      (data_header[1] << 8) + data_header[2]
        protocol = data_header[3] 

        if protocol > 2: # reched protocal limit 
            return None ,None

        data = b''
        try: 
            async with timeouts(FOLLOWING_MESSAGE_TIMEOUT):
                while len(data) < data_length:
                    data += await self._loop.sock_recv(
                                client, data_length - len(data))
        except (ConnectionResetError ,asyncio.TimeoutError): 
            client.close() ;return None ,None

        return data , protocol


class rpc_server(rpc_base):

    '''
    main problem in building a python rpc is in consideration of performance tradeof  ,it's diffcult for us to maintain some high level data structures and inplementing some complex control algrisms with magical functions.
    '''
    async def _recv_magiccall(magic_code):
        return pickle.loads(magic_code[0])


    @autocheck
    def __init__(   self , 
                    host:str = '' ,
                    port:int = 0 ,
                    allow_pickle:bool = True,
                    unstable_network:bool = False
                ):
        super(rpc_server, self).__init__()

        self._server_sock = self.__class__.create_socket(host , port ,True)
        self._unstable_network = unstable_network
        self._request_buffer = {}
        self._pool_lock = RLock()
        self._flow_counting = {}
        self._func_infos = {}
        self._child_list = list()
        self._isparent = None
        self._allow_pickle = allow_pickle
        if allow_pickle:
            self._selector.append(pickle_selector()) # pickle_selector
            self._func_infos['magiccall'] = self.__class__._recv_magiccall, False ,0 ,0

    @autocheck
    def prefork(self , max_workers:int = None ,bindcore:bool = False):
        '''
        bindcore binds each process to a cpu core specifily
        which helps reduce cache miss ,but limits the flexibility of 
        kernel's tasks scheduling.

        which place you fork matters.
        if you fork after register ,then all process shares a unique overflow
        control lock , by contray if you fork before it , each process will
        have its own lock which means you have max_workers times maximum
        overflow. 
        '''
        self._child_list = list()
        self._isparent = True

        cpu_core_nums = cpu_count()

        if max_workers == None:
            max_workers = cpu_core_nums - 1

        if bindcore == None:
            bindcore = False if (max_workers + 1) < cpu_core_nums else True
            try:
                _ = os.sched_setaffinity # currentrly not avilable on pypy
            except:
                bindcore = False

        if bindcore:           
            self._bindcount = Value('i' ,0) 

        for num in range(max_workers):
            pid = os.fork()
            if pid < 0:
                raise OSError(f"Creating fork process failed.")
            elif pid == 0:
                self._isparent = False ;break
            else:
                self._child_list.append(pid)

        self._pid = os.getpid()

        if bindcore:
            with self._pool_lock:
                if self._bindcount.value < ((max_workers+1) // cpu_core_nums) * cpu_core_nums : 
                    os.sched_setaffinity(0 , (self._bindcount.value , ))
                    self._bindcount.value = (self._bindcount.value + 1) % cpu_core_nums

    @autocheck
    def register(   self ,
                    name:str = None ,
                    timeout:int = 60 ,
                    maximum_flow:int = 0
                ):

        if maximum_flow < 0 :
            raise ValueError(f"Maximum flow must be a unsigned integer or 0.")

        def decorator(func , name=name , maximum_flow=maximum_flow):

            if name == None:
                name = func.__name__

            if iscoroutinefunction(func) and maximum_flow:
                raise Warning(f"Attibute maximum flow control is disigned not to work in asynchronous functions in consideration of performance")

            self._func_infos[name] = [
                            func , 
                            not iscoroutinefunction(func) ,
                            timeout ,
                            maximum_flow
            ]

            if maximum_flow:
                 self._flow_counting[name] = Value('i',0)

            return func

        return decorator

    async def _buffer_time_out(self , request_token) -> None:
        for i in range(3):
            await asyncio.sleep(BUFFER_TIMEOUT_SECONDS)
            if self._request_buffer[request_token] != VARIFY_WORD:
                del self._request_buffer[request_token] ;return 
        else:
            del self._request_buffer[request_token]

    async def _handler_server_sendback(self, client:socket.socket ,data:bytes ,protocol:int):

        # exception was catched inside decoder , returns 0 when error occured.
        type_code ,*args = self._selector[protocol].decode(data)
        # print("incomming message",type_code , *args)

        if type_code == 1:

            request_token , funcname , args , kwargs = args

            # In unstable network ,maintain a buffer preventing repeated request caused by package loss.
            if self._unstable_network:            
                if request_token not in self._request_buffer.keys():
                    self._request_buffer[request_token] = VARIFY_WORD
                    self._loop.create_task(self._buffer_time_out(request_token))
                else:
                    rdata = self._request_buffer[request_token]
                    # Task is still running
                    if rdata == VARIFY_WORD: 
                        return 
                    try:
                        await self._loop.sock_sendall(client, rdata)  ;return 
                    except: client.close()  

            try:  
                # Since it's a rare situation , use try to catch in consideration of avg performance
                try:
                    func , sync ,timeout ,maximum_flow = self._func_infos[funcname]
                except:
                    raise AttributeError(f"Rpc server has no function registered as '{funcname}'.")

                # An async fucntion is called
                if not sync:
                    ret = await func(*args , **kwargs)

                # As for synchronous functions ,they should be run in executor , protected with timeout & incomming requests counting . A lock between process is needed to synch state.
                else:
                    if kwargs != {}:
                        raise AttributeError(f"kwargs {kwargs} are not accepted as input in sync synchronized functions.")

                    if maximum_flow:
                        with self._pool_lock:
                            if maximum_flow < self._flow_counting[funcname].value:
                                raise BusyError("Server currently too busy to run your request.")
                            self._flow_counting[funcname].value += 1

                    # with self._pool_lock:

                    '''
                    By default run_in_executor is called activated in a threadpool ,which means you can't benefits from multi cores .It turns out that since I can't do some amazing hacking and add tiny grain size locks into asyncio.base_futures & concurrent.futures , and we couldn't simple inplement a share process unsafe processpool between process without a Lock ,that will cause pipe broken.The solution we got ,currently ,is to create a thread pool for each single listning process. That makes no good for memory ,nor for latency of handling requests.
                    '''

                    task = self._loop.run_in_executor(self._default_pool ,func ,*args)

                    if timeout:
                        async with timeouts(timeout):
                            ret = await task
                    else:
                        ret = await task

                    if maximum_flow:
                        with self._pool_lock:
                            self._flow_counting[funcname].value -= 1

                # encoding return value
                rdata = self._selector[protocol].encode(2 , request_token , ret)

            except Exception as err:
                rdata = self._selector[protocol].encode(3 ,request_token ,repr(err))

            if self._unstable_network:  
                self._request_buffer[request_token] = rdata
            
        else:
            err = DecodingError("An error occured during server decoding message.")
            # request id is setto 0 inorder to prevent malicious attacks
            rdata = self._selector[protocol].encode(3 ,0 ,repr(err)) 
        
        # sending back message
        try:
            await self._loop.sock_sendall(client ,rdata)
        except OSError:
            client.close()


    async def _handler_message_comin(self , client):

        with client:
            while True:
                
                data , protocol = await self.protocoled_fetch(client)
                
                if data is None: break
                elif not data: continue

                self._loop.create_task(self._handler_server_sendback(client, data ,protocol))


    async def start_serving(self , loop = None , testing = False):
        if loop is None:
            self._loop = asyncio.get_running_loop()
        else:
            self._loop = loop

        self._default_pool = Pool(max_workers=cpu_count())
        
        if self._isparent or self._isparent is None:

            if testing:
                sys.stderr.write("Start test.\n")
                sys.stderr.flush()
            else:
                print(f"Start serving at {self._server_sock.getsockname()}\n")
        while True:
            client , addr = await self._loop.sock_accept(self._server_sock)
            self._loop.create_task(self._handler_message_comin( client))

if sys.version_info < (3, 6):
    raise PyVersionError("This module could only run on python 3.6 or above ,which has advanced asyncio apis.")