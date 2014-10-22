
def clamp_control_range(value):
    value = float(value)
    if value < -1.0:
        return -1.0
    elif value > 1.0:
        return 1.0
    else:
        return value

def sign(x):
    x = float(x)
    if x > 0.0:
        return 1
    elif x < 0.0:
        return -1
    else:
        return 0


class EventQueue(object):
    def __init__(self):
        super(EventQueue, self).__init__()
        self.queue = []
        self.lock = threading.Condition(threading.RLock())

    def add(self, *events):
        self.lock.acquire()
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def add_if_empty(self, *events):
        self.lock.acquire()
        if not self.queue:
            for e in events:
                self.queue.append(e)
        self.lock.release()

    def clear(self):
        self.lock.acquire()
        self.queue = []
        self.lock.notifyAll()
        self.lock.release()

    def replace(self, *events):
        self.lock.acquire()
        self.queue = []
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def wait_until_empty(self):
        self.lock.acquire()
        while self.queue:
            self.lock.wait()
        self.lock.release()

    def process(self):
        self.lock.acquire()
        self.pre_process()
        if self.queue:
            print str(self.queue)
        i = 0
        while i < len(self.queue):
            if self.queue[i]():
                i += 1
            else:
                del self.queue[i]
        self.post_process()
        if not self.queue:
            self.lock.notifyAll()
        self.lock.release()

    def pre_process(self):
        pass

    def post_process(self):
        pass

class RunAfterTime(object):
    def __init__(self, seconds, action, tick_length_seconds):
        super(RunAfterTime, self).__init__()
        self.ticks = int(seconds / tick_length_seconds)
        self.action = action

    def __call__(self):
        if self.ticks == 0:
            self.action()
            return False
        else:
            self.ticks -= 1
            return True

class RepeatingAction(object):
    def __init__(self, seconds, action, tick_length_seconds):
        super(RepeatingAction, self).__init__()
        self.init_ticks = int(seconds / tick_length_seconds)
        self.ticks = self.init_ticks
        self.action = action

    def __call__(self):
        if self.ticks == 0:
            self.action()
            self.ticks = self.init_ticks
        else:
            self.ticks -= 1
        return True

class RunAfterCondition(object):
    def __init__(self, cond, action):
        super(RunAfterCondition, self).__init__()
        self.cond = cond
        self.action = action

    def __call__(self):
        if self.cond():
            self.action()
            return False
        else:
            return True
