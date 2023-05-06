import gc
import time
import math
import machine
import network
import ntptime
import settings

# ESP8266 based sunrise alarm clock for Mirabella Genio Wi-Fi 7W LED Tube Lamp
# NOTE: These pins match hardware for an esp-12 transplanted unit.
redPwm = machine.PWM(machine.Pin(4), freq=1000)
greenPwm = machine.PWM(machine.Pin(12), freq=1000)
bluePwm = machine.PWM(machine.Pin(14), freq=1000)
whitePwm = machine.PWM(machine.Pin(5), freq=1000)

sw = machine.ADC(0)

def localtime():
    import time
    now = time.time()

    offset = 0
    for tz in settings.tzinfo:
        if tz[0] > now:
            break
        offset = tz[1]
    return now + offset

# https://andi-siess.de/rgb-to-color-temperature/
kelvin_table = {
    1000: (255, 56, 0),
    1100: (255, 71, 0),
    1200: (255, 83, 0),
    1300: (255, 93, 0),
    1400: (255, 101, 0),
    1500: (255, 109, 0),
    1600: (255, 115, 0),
    1700: (255, 121, 0),
    1800: (255, 126, 0),
    1900: (255, 131, 0),
    2000: (255, 138, 18),
    2100: (255, 142, 33),
    2200: (255, 147, 44),
    2300: (255, 152, 54),
    2400: (255, 157, 63),
    2500: (255, 161, 72),
    2600: (255, 165, 79),
    2700: (255, 169, 87),
    2800: (255, 173, 94),
    2900: (255, 177, 101),
    3000: (255, 180, 107),
    3100: (255, 184, 114),
    3200: (255, 187, 120),
    3300: (255, 190, 126),
    3400: (255, 193, 132),
    3500: (255, 196, 137),
    3600: (255, 199, 143),
    3700: (255, 201, 148),
    3800: (255, 204, 153),
    3900: (255, 206, 159),
    4000: (255, 209, 163),
    4100: (255, 211, 168),
    4200: (255, 213, 173),
    4300: (255, 215, 177),
    4400: (255, 217, 182),
    4500: (255, 219, 186),
    4600: (255, 221, 190),
    4700: (255, 223, 194),
    4800: (255, 225, 198),
    4900: (255, 227, 202),
    5000: (255, 228, 206),
    5100: (255, 230, 210),
    5200: (255, 232, 213),
    5300: (255, 233, 217),
    5400: (255, 235, 220),
    5500: (255, 236, 224),
    5600: (255, 238, 227),
    5700: (255, 239, 230),
    5800: (255, 240, 233),
    5900: (255, 242, 236),
    6000: (255, 243, 239),
    6100: (255, 244, 242),
    6200: (255, 245, 245),
    6300: (255, 246, 247),
    6400: (255, 248, 251),
    6500: (255, 249, 253),
    6600: (254, 249, 255),
    6700: (252, 247, 255),
    6800: (249, 246, 255),
    6900: (247, 245, 255),
    7000: (245, 243, 255),
    7100: (243, 242, 255),
    7200: (240, 241, 255),
    7300: (239, 240, 255),
    7400: (237, 239, 255),
    7500: (235, 238, 255),
    7600: (233, 237, 255),
    7700: (231, 236, 255),
    7800: (230, 235, 255),
    7900: (228, 234, 255),
    8000: (227, 233, 255),
    8100: (225, 232, 255),
    8200: (224, 231, 255),
    8300: (222, 230, 255),
    8400: (221, 230, 255),
    8500: (220, 229, 255),
    8600: (218, 229, 255),
    8700: (217, 227, 255),
    8800: (216, 227, 255),
    8900: (215, 226, 255),
    9000: (214, 225, 255),
    9100: (212, 225, 255),
    9200: (211, 224, 255),
    9300: (210, 223, 255),
    9400: (209, 223, 255),
    9500: (208, 222, 255),
    9600: (207, 221, 255),
    9700: (207, 221, 255),
    9800: (206, 220, 255),
    9900: (205, 220, 255),
    10000: (207, 218, 255),
    10100: (207, 218, 255),
    10200: (206, 217, 255),
    10300: (205, 217, 255),
    10400: (204, 216, 255),
    10500: (204, 216, 255),
    10600: (203, 215, 255),
    10700: (202, 215, 255),
    10800: (202, 214, 255),
    10900: (201, 214, 255),
    11000: (200, 213, 255),
    11100: (200, 213, 255),
    11200: (199, 212, 255),
    11300: (198, 212, 255),
    11400: (198, 212, 255),
    11500: (197, 211, 255),
    11600: (197, 211, 255),
    11700: (197, 210, 255),
    11800: (196, 210, 255),
    11900: (195, 210, 255),
    12000: (195, 209, 255)}

def lerp(a: float, b: float, t: float) -> float: return (1 - t) * a + t * b
def getColour(ct : int, br : float):
    min_rgb = None
    max_rgb = None
    for k, rgb in sorted(kelvin_table.items()):
        if k == ct:
            min_rgb = (rgb, k)
            break
        elif k < ct:
            min_rgb = (rgb, k)
            continue
        else:
            max_rgb = (rgb, k)
            break

    rgb = None
    if min_rgb is not None and max_rgb is not None:
        ((rmin, gmin, bmin), kmin) = min_rgb
        ((rmax, gmax, bmax), kmax) = max_rgb
        kt = (ct - kmin) / (kmax - kmin)
        rgb = (lerp(rmin, rmax, kt), lerp(gmin, gmax, kt), lerp(bmin, bmax, kt))
    elif min_rgb is not None:
        (rgb, _) = min_rgb
    elif max_rgb is not None:
        (rgb, _) = max_rgb

    return rgb

def setColour(ct : int, br : float):
    (r, g, b) = getColour(ct, br)
    setColourRGBW(r / 255.0, g / 255.0, b / 255.0, br)

def setColourRGBW(r, g, b, w):
    r = int(r * 1023.0)
    g = int(g * 1023.0)
    b = int(b * 1023.0)
    w = int(w * 1023.0)
    redPwm.duty(r)
    greenPwm.duty(g)
    bluePwm.duty(b)
    whitePwm.duty(w)

def sunriseSequence():
    a = 1000
    b = 10000
    duration = 3600.0
    # Fade ct over an hour
    interval = duration / (b - a)
    br = 0
    br_step = (1.0 - br) / (b - a)
    for ct in range(a, b):
        setColour(ct, br*br)
        br += br_step
        time.sleep(interval)
    setColour(b, 1.0)
    time.sleep(15*60)
    setColour(a, 0.0)

def bedtimeSequence():
    (r, g, b) = settings.colour
    duration = 3600
    br = 0.4
    br_step = br / duration
    for i in range(0, duration):
        setColourRGBW((r / 255.0) * br, (g / 255.0) * br, (b / 255.0) * br, 0);
        br -= br_step
        time.sleep(1)
    setColourRGBW(0, 0, 0, 0)

def getNextAlarmObject(alarm):
    nextTime = localtime()
    alarmDaySeconds = (alarm['time'][0] * 60 * 60) + (alarm['time'][1] * 60)

    while True:
        nextLocalTime = time.localtime(nextTime)
        nextDaySeconds = (nextLocalTime[3] * 60 * 60) + (nextLocalTime[4] * 60) + nextLocalTime[5]

        if nextDaySeconds > alarmDaySeconds:
            nextTime += (86400 - nextDaySeconds)
        elif nextLocalTime[6] not in alarm['days']:
            nextTime += (86400 - nextDaySeconds)
        else:
            nextTime += alarmDaySeconds - nextDaySeconds
            break

    return (nextTime, alarm['action'])

def getNextAlarm():
    nextAlarm = None
    for alarm in settings.alarm:
        nextAlarmCandidate = getNextAlarmObject(alarm);
        if nextAlarm is None:
            nextAlarm = nextAlarmCandidate
        elif nextAlarmCandidate[0] < nextAlarm[0]:
            nextAlarm = nextAlarmCandidate
    return nextAlarm

if __name__ == "__main__":
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    (nextAlarmTime, alarmFn) = getNextAlarm()

    while True:
        gc.collect()

        deltaNextAlarm = (nextAlarmTime - 3600) - localtime()
        if deltaNextAlarm > 3600:
            time.sleep(3600)
            ntptime.settime()
        else:
            time.sleep(deltaNextAlarm)
            locals()[alarmFn]()
            (nextAlarmTime, alarmFn) = getNextAlarm()
