import sys
sys.path.append('/home/new/LinuxDemo')

import asyncio
import easyrpc
import random
import time

s = easyrpc.rpc_server(port = 30000 , unstable_network = True)

@s.register()
async def test_async_1(n):
	return n

# random time sendback
@s.register()
async def test_async_2(n):
	asyncio.sleep(random.random() // 5)
	return n

@s.register()
def test_sync_1(n):
	return n ** 2

@s.register()
def test_sync_2(n):
	time.sleep(random.random() // 10)
	return n

# cpu_bound
@s.register()
def test_fib(n):
	if n < 2:
		return n
	else:
		return test_fib(n-1) + test_fib(n-2)

@s.register()
async def test_params(key,value):
	return value+1 , key-1

# s.prefork()

loop = asyncio.get_event_loop()
try:
	loop.run_until_complete(s.start_serving(loop ,testing=True))
except BaseException:
	os.wait()
