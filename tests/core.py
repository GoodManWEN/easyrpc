import time
import psutil
import signal
import py

from xprocess import ProcessStarter

server_path = py.path.local(__file__).dirpath("server.py")

class Starter(ProcessStarter):
    pattern = "Start test."
    args = ['python3', server_path]

class timeout_limit:

    def __init__(self , limits):
        self._limits = limits

    def __enter__(self):
        self._start_time = time.time()

    def __exit__(self ,exc_type, exc_val, exc_tb):
        assert time.time()-self._start_time <= self._limits

def mod_terminate(xprocessinfo):

    if not xprocessinfo.pid or not xprocessinfo.isrunning():
        return 0

    timeout = 10

    try:
        parent = psutil.Process(xprocessinfo.pid)
        children = parent.children(recursive=True)
        children.append(parent)
        for p in children:
            p.send_signal(signal.SIGTERM)
        try:
            parent.wait(timeout=timeout/2)
        except psutil.TimeoutExpired:
            parent.kill()
            parent.wait(timeout=timeout/2)
    except psutil.Error:
        return -1

    return 1