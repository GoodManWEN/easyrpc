import asyncio
import sys

from inspect import signature 
from functools import wraps
from types import TracebackType
from typing import Optional, Type, Any  # noqa



__version__ = '3.0.1'

PY_37 = sys.version_info >= (3, 7)



def autocheck(func):
    '''

    Datatype auto check ,supports types and values.
    Checkout PEP484 for more information.

    '''
    trace = signature(func)
    reference = func.__annotations__

    def not_instance(value ,target ,name ,reponame):
        if not isinstance(target[name],(tuple,dict)):
            values , types_ = (), target[name]
        else:
            values = tuple(filter(lambda x:False if isinstance(x,type) else True ,target[name] ))
            # due to filtering by set ,list* could not be used in type hint
            types_ = tuple( set(target[name]) - set(values) )
        if value in values or isinstance(value, types_):
            return ;
        raise TypeError(f'Argument "{reponame}" must be type {target[name]}')

    @wraps(func)
    def wrapper(*args, **kwargs):
        for name,value in trace.bind(*args, **kwargs).arguments.items():
            if name in reference:
                if isinstance(value ,tuple):
                    for value_value in value:
                        not_instance(value_value, reference, name, name)
                elif isinstance(value ,dict):
                    for name_name, value_value in value.items():
                        not_instance(value_value, reference, name, name_name)
                else:
                    not_instance(value, reference, name, name)      
        ret = func(*args, **kwargs)
        if 'return' not in reference or isinstance(ret,reference['return']):
            return ret
        raise TypeError(f'Return type of {func.__name__} must be type {reference["return"]}')
    return wrapper



class timeouts:
    """timeout context manager.
    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:
    >>> with timeout(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()
    timeout - value in seconds or None to disable timeout logic
    loop - asyncio compatible event loop
    """
    def __init__(self, timeout: Optional[float],
                 *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._timeout = timeout
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._task = None  # type: Optional[asyncio.Task[Any]]
        self._cancelled = False
        self._cancel_handler = None  # type: Optional[asyncio.Handle]
        self._cancel_at = None  # type: Optional[float]

    def __enter__(self) -> 'timeout':
        return self._do_enter()

    def __exit__(self,
                 exc_type: Type[BaseException],
                 exc_val: BaseException,
                 exc_tb: TracebackType) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    async def __aenter__(self) -> 'timeout':
        return self._do_enter()

    async def __aexit__(self,
                        exc_type: Type[BaseException],
                        exc_val: BaseException,
                        exc_tb: TracebackType) -> None:
        self._do_exit(exc_type)

    @property
    def expired(self) -> bool:
        return self._cancelled

    @property
    def remaining(self) -> Optional[float]:
        if self._cancel_at is not None:
            return max(self._cancel_at - self._loop.time(), 0.0)
        else:
            return None

    def _do_enter(self) -> 'timeout':
        # Support Tornado 5- without timeout
        # Details: https://github.com/python/asyncio/issues/392
        if self._timeout is None:
            return self

        self._task = current_task(self._loop)
        if self._task is None:
            raise RuntimeError('Timeout context manager should be used '
                               'inside a task')

        if self._timeout <= 0:
            self._loop.call_soon(self._cancel_task)
            return self

        self._cancel_at = self._loop.time() + self._timeout
        self._cancel_handler = self._loop.call_at(
            self._cancel_at, self._cancel_task)
        return self

    def _do_exit(self, exc_type: Type[BaseException]) -> None:
        if exc_type is asyncio.CancelledError and self._cancelled:
            self._cancel_handler = None
            self._task = None
            raise asyncio.TimeoutError
        if self._timeout is not None and self._cancel_handler is not None:
            self._cancel_handler.cancel()
            self._cancel_handler = None
        self._task = None
        return None

    def _cancel_task(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._cancelled = True


def current_task(loop: asyncio.AbstractEventLoop) -> 'asyncio.Task[Any]':
    if PY_37:
        task = asyncio.current_task(loop=loop)  # type: ignore
    else:
        task = asyncio.Task.current_task(loop=loop)
    if task is None:
        # this should be removed, tokio must use register_task and family API
        if hasattr(loop, 'current_task'):
            task = loop.current_task()  # type: ignore

    return task