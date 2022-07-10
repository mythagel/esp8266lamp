import machine
import ntptime

ww = machine.PWM(machine.Pin(0), freq=1000)
cw = machine.PWM(machine.Pin(2), freq=1000)

ww.duty(0)
cw.duty(512)

#    cold_white_color_temperature: 5700 K
#    warm_white_color_temperature: 3000 K

# TODO just have functions to write config files to set the timezone offsets / alarm time

wwct = 3000
cwct = 5700

ct = lerp(wwct, cwct, 0.0)
br = 0.0

def lerp(a: float, b: float, t: float) -> float:
    return (1 - t) * a + t * b

def localtime():
    # TODO
    pass
