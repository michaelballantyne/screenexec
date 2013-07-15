import imp, argparse, screenexec, subprocess, os, threading, collections
from multiprocessing.managers import BaseManager


class Window(object):
    def __init__(self):
        self._tasks = []

    def do(self, do_func, notify=None, after=None):
        self._tasks.append((do_func, notify, after)) 


_windows = []
def windows(count):
    new_windows = []
    for i in range(count):
        window = Window()
        new_windows.append(window)
        _windows.append(window)
    return new_windows

def parse_args():
    parser = argparse.ArgumentParser("Run commands in parallel in screen.")
    parser.add_argument("task_file", help="Python script with window and task definitions")
    parser.add_argument("--window", type=int, default=None)
    return parser.parse_args()

def execute_tasks(window):
    class EventManager(BaseManager):
        pass

    EventManager.register('get_event')

    m = EventManager(address=('127.0.0.1', 50000), authkey='abc')
    m.connect()

    for task in window._tasks:
        if task[2]:
            m.get_event(task[2]).wait()
        task[0]()
        if task[1]:
            m.get_event(task[1]).set()


def open_windows(count, task_file):
    class EventManager(BaseManager):
        pass

    e = collections.defaultdict(lambda: threading.Event())
    EventManager.register('get_event', callable=lambda n: e[n])

    m = EventManager(address=('127.0.0.1', 50000), authkey='abc')
    m.start()


    s = subprocess.Popen(['screen', '-S', 'screenexec'])
    subprocess.call(['screen', '-S', 'screenexec', '-X', '-p', '0', 'stuff', "clear\n"])
    subprocess.call(['screen', '-S', 'screenexec', '-X', '-p', '0', 'stuff', "python " + os.path.realpath(__file__) + " " + os.path.realpath(task_file) + " --window 0\n"])

    for i in range(1, count):
        subprocess.call(['screen', '-S', 'screenexec', '-X', 'screen'])
        subprocess.call(['screen', '-S', 'screenexec', '-X', '-p', str(i), 'stuff', "clear\n"])
        subprocess.call(['screen', '-S', 'screenexec', '-X', '-p', str(i), 'stuff', "python " + os.path.realpath(__file__) + " " + os.path.realpath(task_file) + " --window " + str(i) + "\n"])

    subprocess.call(['screen', '-S', 'screenexec', '-X', 'select', '0'])
    s.wait()

if __name__ == "__main__":
    args = parse_args() 
    
    imp.load_source('taskfile', args.task_file)
    windows = screenexec._windows

    if args.window is not None:
        execute_tasks(windows[args.window])
    else:
        open_windows(len(windows), args.task_file)
