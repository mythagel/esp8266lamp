import time
import math
import machine
import ntptime
import settings

warmPwm = machine.PWM(machine.Pin(5), freq=1000)
coolPwm = machine.PWM(machine.Pin(4), freq=1000)

# TODO just have functions to write config files to set the timezone offsets / alarm time

# TODO Startup indication

# 3000 - 4350 = 100% ww, 0 -> 100% cw
# 4351 - 5700 = 100% cw, 100 -> 0% ww
def clamp(x : float): return max(0.0, min(x, 1.0))
def setColour(ct : int, br : float):
    # ww = 3000, cw = 5700
    ww = clamp(1 - (ct - 4351) / (5700 - 4351))
    cw = clamp((ct - 3000) / (4350 - 3000))
    br = clamp(br)
#    print(ct, int(ww * 1023 * br), int(cw * 1023 * br))

    # TODO brightness probably isn't linear
    warmPwm.duty(int(ww * 1023 * br))
    coolPwm.duty(int(cw * 1023 * br))

def localtime():
    import time
    now = time.time();

    offset = 0;
    for tz in settings.tzinfo:
        if tz[0] > now:
            break
        offset = tz[1]
    return time.localtime(now + offset)

#now = localtime()
#if now[6] in settings.alarm['days']:    # valid alarm day
#    pass


# Fade ct over an hour
interval = 3600.0 / (5700 - 3000)   # TODO 3600.0
br_step = 1.0 / (5700 - 3000)
br = 0
for ct in range(3000, 5700):
#    setColour(ct, br);
    br = br + br_step
#    time.sleep(interval)

setColour(3000, 0.0);
