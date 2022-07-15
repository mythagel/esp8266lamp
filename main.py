import time
import math
import machine
import ntptime
import settings

# ESP8266 based sunrise alarm clock for Arlec Grid Connect Smart 9W CCT LED Downlight (ALD092CHA)
# NOTE: These pins are custom since the version I have didn't originally have an ESP8266 in it.
warmPwm = machine.PWM(machine.Pin(5), freq=1000)
coolPwm = machine.PWM(machine.Pin(4), freq=1000)

def localtime():
    import time
    now = time.time()

    offset = 0
    for tz in settings.tzinfo:
        if tz[0] > now:
            break
        offset = tz[1]
    return now + offset

# 3000 - 4350 = 100% ww, 0 -> 100% cw
# 4351 - 5700 = 100% cw, 100 -> 0% ww
def clamp(x : float): return max(0.0, min(x, 1.0))
def setColour(ct : int, br : float):
    # ww = 3000, cw = 5700
    ww = clamp(1 - (ct - 4351) / (5700 - 4351))
    cw = clamp((ct - 3000) / (4350 - 3000))
    br = clamp(br*br)
    warmPwm.duty(int(ww * 1023 * br))
    coolPwm.duty(int(cw * 1023 * br))

def sunriseSequence(duration : float):
    # Fade ct over an hour
    interval = duration / (5700 - 3000)
    br_step = 1.0 / (5700 - 3000)
    br = 0
    for ct in range(3000, 5700):
        setColour(ct, br)
        br += br_step
        time.sleep(interval)
    setColour(5700, 1.0)

def getNextAlarm():
    nextTime = localtime()
    alarmDaySeconds = (settings.alarm['time'][0] * 60 * 60) + (settings.alarm['time'][1] * 60)

    while True:
        nextLocalTime = time.localtime(nextTime)
        nextDaySeconds = (nextLocalTime[3] * 60 * 60) + (nextLocalTime[4] * 60) + nextLocalTime[5]

        if nextDaySeconds > alarmDaySeconds:
            nextTime += (86400 - nextDaySeconds)
        elif nextLocalTime[6] not in settings.alarm['days']:
            nextTime += (86400 - nextDaySeconds)
        else:
            nextTime += alarmDaySeconds - nextDaySeconds
            break

    return nextTime

if __name__ == "__main__":
    nextAlarmTime = getNextAlarm()

    while True:
        deltaNextAlarm = nextAlarmTime - localtime()
        if deltaNextAlarm > 3600:
            time.sleep(3600)
            ntptime.settime()
        else:
            sunriseSequence(3600.0)
            time.sleep(120)
            setColour(3000, 0.0)
            nextAlarmTime = getNextAlarm()
