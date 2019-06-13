from msgpack import packb ,unpackb
from pickle import loads ,dumps
from .exceptions import *


class base_selector:
    """docstring for base_selector"""
    def __init__(self , idf_code):
        self._idf_code = idf_code
        self._serializer = None

    def encode(self , message_type:int , request_token:int, *args) -> bytes:

        try:
            if message_type == 1:
                data = self._serializer({
                        "t" : 1,
                        "n" : request_token,
                        "f" : args[0],
                        "a" : args[1],
                        "kw": args[2]
                    })
            elif message_type == 2:
                data = self._serializer({
                        "t" : 2,
                        "n" : request_token,
                        "v" : args[0]
                    })
            elif message_type == 3:
                data = self._serializer({
                        "t" : 3,
                        "n" : request_token,
                        "err": args[0]
                    })

            data_length = len(data)

            if data_length > 16777215:
                raise OverflowError("Input message too long to serialze")

            header = (chr(data_length // 65536) + chr(data_length // 256) + chr(data_length % 255) + chr(self._idf_code)).encode()
            return header + data
        except Exception as err:
            raise SerializeError(err)

    def decode(self):
        ''' due to msgpack transform string types into bytes ,recv method should be written  respectively'''

    

class msgpack_selector(base_selector):

    def __init__(self):
        super(msgpack_selector, self).__init__( idf_code = 0 )

        self._serializer = packb


    def decode(self , data):

        tostr = lambda x: x.decode('utf-8') if type(x) is bytes else x 

        try:

            message = unpackb(data)
            message_type = message[b't']

            if message_type == 1:

                _ ,  request_token ,funcname ,args ,kwargs = message.values()
                funcname = funcname.decode('utf-8')
                args = tuple(map(tostr , args))
                kwargs = dict(zip(
                         map(tostr ,kwargs.keys()) 
                        ,map(tostr , kwargs.values()) 
                        ))
                return _ , request_token , funcname , args , kwargs

            elif message_type == 2:

                _ , request_token ,values = message.values()

                if type(values) is bytes:
                    values = values.decode('utf-8')
                elif type(values) is tuple:
                    values = tuple(map(tostr , values))

                return _ , request_token ,values

            elif message_type == 3:

                _ , request_token ,errrepr = message.values()
                errrepr = errrepr.decode()
                return _ , request_token ,errrepr
            else:
                # message type error
                return (0 ,)
        except :
            return (0 ,)

class pickle_selector(base_selector):

    def __init__(self):
        super(pickle_selector, self).__init__( idf_code = 1 )

        self._serializer = dumps

    def decode(self, data):

        try:
            message = loads(data)
            message_type = message['t']

            if message_type == 1:
                _ ,  request_token ,funcname ,args ,kwargs = message.values()
                return request_token ,funcname ,args ,kwargs
            elif message_type == 2:
                _ , request_token, values = message.values()
                return _ ,request_token ,values
            elif message_type == 3:
                _ , request_token, errrepr= message.values()
                return _ , request_token ,errrepr
            else :
                # message type error
                return (0 ,)
        except:
            return (0 ,)

