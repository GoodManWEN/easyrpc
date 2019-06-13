import sys
sys.path.append('../')

import easyrpc
import pytest
import time
import asyncio
import random
import time

from multiprocessing import cpu_count
from xprocess import ProcessStarter
from core import Starter , timeout_limit , mod_terminate

@pytest.mark.asyncio
async def test_activated(xprocess):
    xprocess.ensure("server", Starter,restart=True)

@pytest.mark.asyncio
async def test_client(xprocess):
    c = easyrpc.rpc_client(port = 30000)

    # preexciting
    for i in range(50):
        ret = await c.test_async_1(10)

    # single async call
    with timeout_limit(0.1):
        assert await c.test_async_1(10) == 10

    # multiple async call
    with timeout_limit(0.3):
        tasks = (c.test_async_2(i) for i in range(100))
        ret = await asyncio.gather(*tasks)
        assert ret == [i for i in range(100)]

    # single sync call
    with timeout_limit(0.1):
        randnum = random.randint(0,9999)
        assert await c.test_sync_1(randnum) == (randnum ** 2)

    # multiple sync call
    with timeout_limit(0.3):
        tasks = (c.test_sync_2(i) for i in range(100))
        ret = await asyncio.gather(*tasks)
        assert ret == [i for i in range(100)]

    # cpu bound
    start_time = time.time()
    await c.test_fib(28)
    single_call_time = time.time()-start_time

    with timeout_limit(single_call_time * max(2,cpu_count()*0.75)):
        tasks = (c.test_fib(28) for i in range(cpu_count()))
        ret = await asyncio.gather(*tasks)
        assert ret == [317811] * cpu_count()

    # params test
    assert await c.test_params(1,2) == [3 ,0]
    assert await c.test_params(key = 1,value = 2) == [3 ,0]
    assert await c.test_params(1,value = 2) == [3 ,0]

    with pytest.raises(Exception):
        await c.no_this_func()

    with pytest.raises(Exception):
        await c.test_params(1,2,3)

    with pytest.raises(Exception):
        await c.test_params(key = 1 , value = 2 , nope = 3)

    # large package
    await c.test_async_1([b'1'*1_000_000]) == [b'1'*1_000_000]

    # sync call
    assert await c.test_async_1(10) == c.test_async_1(10,sync=True)
    assert await c.test_sync_1(10) == c.test_sync_1(10,sync=True)

    # shutdown
    mod_terminate(xprocess.getinfo("server"))
