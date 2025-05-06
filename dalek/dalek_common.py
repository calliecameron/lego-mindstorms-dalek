import threading
import re


def espeakify(text):
    # Espeak can't pronounce 'Dalek', so force it to say 'Dahlek'
    dalek = re.compile(re.escape("Dalek"), re.IGNORECASE)
    return dalek.sub("Dahlek", text)


def sound_filename(text):
    text = text.lower().replace(" ", "-")
    return ''.join(
        [c if re.match("^[a-z0-9-]$", c) else "" for c in text])


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
    def __init__(self, verbose=False):
        super(EventQueue, self).__init__()
        self.queue = []
        self.lock = threading.Condition(threading.RLock())
        self.verbose = verbose

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
        if self.verbose and self.queue:
            print self.queue
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

    def __repr__(self):
        return "RunAfterTime %d [%s]" % (self.ticks, self.action)


class RepeatingAction(object):
    def __init__(self, seconds, action, tick_length_seconds):
        super(RepeatingAction, self).__init__()
        self.init_ticks = int(seconds / tick_length_seconds)
        self.ticks = 0
        self.action = action

    def __call__(self):
        if self.ticks == 0:
            self.action()
            self.ticks = self.init_ticks
        else:
            self.ticks -= 1
        return True

    def __repr__(self):
        return "RepeatingAction %d %d [%s]" % (
            self.init_ticks, self.ticks, self.action)


class DurationAction(object):
    def __init__(self, seconds, start_action, end_action, tick_length_seconds):
        super(DurationAction, self).__init__()
        self.start_action = start_action
        self.end_timer = RunAfterTime(seconds, end_action, tick_length_seconds)

    def __call__(self):
        if self.start_action:
            self.start_action()
            self.start_action = None

        return self.end_timer()

    def __repr__(self):
        return "DurationAction [%s, %s]" % (self.start_action, self.end_timer)


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

    def __repr__(self):
        return "RunAfterCondition [%s, %s]" % (self.cond, self.action)
