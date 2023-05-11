from dataclasses import dataclass
import time
import threading
from MiscLib import *

@dataclass
class FiberInfo:
    fiber_name        : str
    fiber             : callable
    args              : tuple
    interval          : int
    activation_status : bool
    running_status    : bool

class FiberScheduler:
    def __init__(self):
        self.fiber_list       = {}
        self.fiber_last_trigger_time = {}
        self.is_running              = False

    def RegisterFiber(self, fiber, args=None, interval=None, activation_status=False):
        self.fiber_list[fiber.__name__] = FiberInfo(fiber.__name__, fiber, args, interval, activation_status, False)

    def ActivateFiber(self, fiber):
        self.fiber_list[fiber.__name__].activation_status = True
        DebugLog(LOG_DEBUG, 'Activated fiber {}'.format(fiber.__name__))

    def DeactivateFiber(self, fiber):
        while(self.IsFiberRunning(fiber)):
            pass
        self.fiber_list[fiber.__name__].activation_status = False
        DebugLog(LOG_DEBUG, 'Deactivated fiber {}'.format(fiber.__name__))

    def IsFiberRunning(self, fiber):
        return self.fiber_list[fiber.__name__].running_status

    def RunFiberLoop(self):
        self.is_running = True
        while(self.is_running):
            for fiber_name, fiber_info in self.fiber_list.items():
                if (self.is_running == False):
                    break
                elif fiber_info.activation_status == False:
                    continue
                elif (fiber_info.interval != None):
                    if fiber_name not in self.fiber_last_trigger_time:
                        self.fiber_last_trigger_time[fiber_name] = time.time()
                    if (time.time() - self.fiber_last_trigger_time[fiber_name]) < fiber_info.interval:
                        continue

                self.fiber_last_trigger_time[fiber_name] = time.time()
                fiber_info.running_status = True
                if fiber_info.args == None:
                    fiber_info.fiber()
                else:
                    fiber_info.fiber(fiber_info.args)
                fiber_info.running_status = False
                time.sleep(0.10)

    def Run(self):
        DebugLog(LOG_DEBUG, 'Scheduler service started...')
        self.fiber_scheduler_thread = threading.Thread(target=self.RunFiberLoop)
        self.fiber_scheduler_thread.setDaemon(True)
        self.fiber_scheduler_thread.start()

    def Resume(self):
        DebugLog(LOG_DEBUG, 'Scheduler service resumed...')
        self.Run()

    def Stop(self):
        DebugLog(LOG_DEBUG, 'Scheduler service stopped...')
        self.is_running = False
