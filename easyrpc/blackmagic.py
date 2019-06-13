import sys
import re
import inspect
from typing import Callable
from functools import partial

from .aside import autocheck

'''
Pickle is a magic library python provides serialize service ,which is a stack describe language in essence. It maks it possible to share high level objects between process ,however it's low performance comparing to msgpack and not secure against erroneous maliciously constructed data.
Pickle protocol is defaultly disabled in easyrpc.

We provides a magic call interface using pickle which allows you to register function from clients to a server ,of cource it's extremely unsafe ground floor , but it's fun to use.
'''

'''
This library is aimed to let you use rpc easily.
Which allows you to register both synchronous and asynchronous functions ,and will unifiedly provides services asynchronously.
Which will be usefull if you are using aiohttp but you want to write your database affairs synchronously, or if you are using django but you want some high performance asynchronous database affairs ,or if you want to take advantage of pypy or multi cores's hight performance etc.
'''

'''
Since synchronous is trigered in a encapsulation of processpoll ,which takes four times of ipc (client -> server -> subprocess -> back1 -> back2) and maybe also need to create a new process , which could take a long period of upto 1ms.Thus ,this method is recomended if and only if you can save more time than that ,for example if you would like to compute some kind of recursived fibonacci sequence with a maximum depth of 40 using pypy etc.
'''

class MagicianAssistant:

    def __init__(self , code):
        self._code = code

def magicwarp(func:Callable) -> MagicianAssistant:
    # solution below has some namespace problem
    '''func_id = sys._getframe().f_locals['func']
    for key ,ids in sys._getframe().f_globals.items():
        if ids == func_id:
            target_name = key ;break
    else:
        raise AttributeError("Didnot find lambda function")'''
    if func.__name__ != '<lambda>':
        raise TypeError('Currently only lambda functions is supported for magic call')
    active = inspect.getframeinfo(inspect.currentframe().f_back)[3][0]
    active = active[active.index(".magicwarp(")+11:]
    target_name = re.match('[a-zA-Z_$][a-zA-Z0-9_$]*',active)
    if target_name:
        target_name = target_name.group()
    else:
        raise AttributeError("Didnot find input name")
    with open(sys.argv[0]) as f:
        cont = f.read()
    pat = re.compile(f'{target_name}.*=.*lambda.*:.+?\n').findall(cont)
    if pat:
        for mat in pat:
            if 'target_name' not in mat:
                targstr = mat[:-1] 
                targstr = targstr[targstr.index('=')+1:].strip()   ; break
        else:
            raise AttributeError("Didnot find lambda function")
    else:
        raise AttributeError("Didnot find lambda function")

    return MagicianAssistant(targstr)

@autocheck
def magiccall(self, assistant:MagicianAssistant) -> Callable:
    def warper(*args , **kwargs):
        if kwargs:
            raise AttributeError("kwargs not allowed in magiccall")
        if args:
            args = args[0]
            if isinstance(args,int):
                args = f'I{args}\n'
            elif isinstance(args,str):
                args = f'V{args}\np0\n'
        else:
            args = ""
        sending = b'\x80\x01' + f"c__builtin__\neval\n(S'{assistant._code}'\ntR({args}tR.".encode()
        # print(f"sending magic call : {sending}")
        return partial(self._sync_call , funcname = 'magiccall' , args = ([sending],),kwargs = {})()
    return warper