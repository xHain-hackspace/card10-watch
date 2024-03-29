"""
Original remarks:
This project is inspired by yrlfs digiclk and base functionality (clock) is taken from there.
https://github.com/Ferdi265/card10-digiclk

Thanks to lortas for the battery rendering code
End original remarks

The current code was based on https://github.com/christian-draeger/watch-plus-plus
"""

import buttons
import display
import os
import utime
import light_sensor
import power
import math
import bhi160
bhi = bhi160.BHI160Orientation()
viewing_event_start_time = utime.time()
viewing_state = 'viewing'
last_y_angle = 0


def ceil_div(a, b):
    return (a + (b - 1)) // b


def tip_height(w):
    return ceil_div(w, 2) - 1


def draw_tip(d, x, y, w, c, invert=False, swapAxes=False):
    h = tip_height(w)
    for dy in range(h):
        for dx in range(dy + 1, w - 1 - dy):
            px = x + dx
            py = y + dy if not invert else y + h - 1 - dy
            if swapAxes:
                px, py = py, px
            d.pixel(px, py, col=c)


def draw_seg(d, x, y, w, h, c, swapAxes=False):
    tip_h = tip_height(w)
    body_h = h - 2 * tip_h

    draw_tip(d, x, y, w, c, invert=True, swapAxes=swapAxes)

    px1, px2 = x, x + (w - 1)
    py1, py2 = y + tip_h, y + tip_h + (body_h - 1)
    if swapAxes:
        px1, px2, py1, py2 = py1, py2, px1, px2
    d.rect(px1, py1, px2, py2, col=c)

    draw_tip(d, x, y + tip_h + body_h, w, c, invert=False, swapAxes=swapAxes)


def draw_Vseg(d, x, y, w, l, c):
    draw_seg(d, x, y, w, l, c)


def draw_Hseg(d, x, y, w, l, c):
    draw_seg(d, y, x, w, l, c, swapAxes=True)


def draw_grid_seg(d, x, y, w, l, c, swapAxes=False):
    sw = w - 2
    tip_h = tip_height(sw)

    x = x * w
    y = y * w
    l = (l - 1) * w
    draw_seg(d, x + 1, y + tip_h + 3, sw, l - 3, c, swapAxes=swapAxes)


def draw_grid_Vseg(d, x, y, w, l, c):
    draw_grid_seg(d, x, y, w, l, c)


def draw_grid_Hseg(d, x, y, w, l, c):
    draw_grid_seg(d, y, x, w, l, c, swapAxes=True)


def draw_grid(d, x1, y1, x2, y2, w, c):
    for x in range(x1 * w, x2 * w):
        for y in range(y1 * w, y2 * w):
            if x % w == 0 or x % w == w - 1 or y % w == 0 or y % w == w - 1:
                d.pixel(x, y, col=c)


def draw_grid_7seg(d, x, y, w, segs, c):
    if segs[0]:
        draw_grid_Hseg(d, x, y, w, 4, c)
    if segs[1]:
        draw_grid_Vseg(d, x + 3, y, w, 4, c)
    if segs[2]:
        draw_grid_Vseg(d, x + 3, y + 3, w, 4, c)
    if segs[3]:
        draw_grid_Hseg(d, x, y + 6, w, 4, c)
    if segs[4]:
        draw_grid_Vseg(d, x, y + 3, w, 4, c)
    if segs[5]:
        draw_grid_Vseg(d, x, y, w, 4, c)
    if segs[6]:
        draw_grid_Hseg(d, x, y + 3, w, 4, c)


DIGITS = [
    (True, True, True, True, True, True, False),
    (False, True, True, False, False, False, False),
    (True, True, False, True, True, False, True),
    (True, True, True, True, False, False, True),
    (False, True, True, False, False, True, True),
    (True, False, True, True, False, True, True),
    (True, False, True, True, True, True, True),
    (True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True),
    (True, True, True, True, False, True, True)
]

MONTH_STRING = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_STRING = ["Mo-", "Tu-", "We-", "Th-", "Fr-", "Sa-", "Su-"]

BATTERY_COLOR_GOOD = [0, 230, 0]
BATTERY_COLOR_OK = [255, 215, 0]
BATTERY_COLOR_BAD = [255, 0, 0]


def get_bat_color(v):
    if v > 3.8:
        return BATTERY_COLOR_GOOD
    if v > 3.6:
        return BATTERY_COLOR_OK
    return BATTERY_COLOR_BAD


def render_battery(display, pos_x=140, pos_y=72):
    v = os.read_battery()
    c = get_bat_color(v)

    if not c:
        return
    display.rect(pos_x, pos_y, pos_x + 15, pos_y + 7, filled=True, col=c)
    display.rect(pos_x + 15, pos_y + 2, pos_x + 17, pos_y + 5, filled=True, col=c)
    if v < 4.0:
        display.rect(pos_x + 11, pos_y + 1, pos_x + 14, pos_y + 6, filled=True, col=[0, 0, 0])
    if v < 3.8:
        display.rect(pos_x + 6, pos_y + 1, pos_x + 11, pos_y + 6, filled=True, col=[0, 0, 0])
    if v < 3.6:
        display.rect(pos_x + 1, pos_y + 1, pos_x + 6, pos_y + 6, filled=True, col=[0, 0, 0])
    render_charging(display, pos_x + 6, pos_y)


def render_charging(display, pos_x, pos_y):
    v_in = power.read_chargein_voltage()
    if v_in > 4.0:
        c = [0, 0, 0]
        c_shade = [120, 120, 120]
        display.pixel(pos_x + 1, pos_y, col=c)
        display.pixel(pos_x + 1, pos_y, col=c)
        display.pixel(pos_x + 2, pos_y, col=c_shade)
        display.pixel(pos_x + 1, pos_y + 1, col=c)
        display.pixel(pos_x, pos_y + 1, col=c_shade)
        display.pixel(pos_x + 1, pos_y + 2, col=c)
        display.pixel(pos_x, pos_y + 2, col=c)
        display.pixel(pos_x, pos_y + 3, col=c)
        display.pixel(pos_x + 1, pos_y + 3, col=c)
        display.pixel(pos_x + 2, pos_y + 3, col=c)
        display.pixel(pos_x + 3, pos_y + 3, col=c_shade)
        display.pixel(pos_x + 2, pos_y + 4, col=c)
        display.pixel(pos_x + 3, pos_y + 4, col=c)
        display.pixel(pos_x + 4, pos_y + 4, col=c)
        display.pixel(pos_x + 1, pos_y + 4, col=c_shade)
        display.pixel(pos_x + 3, pos_y + 5, col=c)
        display.pixel(pos_x + 4, pos_y + 5, col=c)
        display.pixel(pos_x + 3, pos_y + 6, col=c)
        display.pixel(pos_x + 4, pos_y + 6, col=c_shade)
        display.pixel(pos_x + 3, pos_y + 7, col=c)
        display.pixel(pos_x + 2, pos_y + 7, col=c_shade)


def render_num(d, num, x):
    draw_grid_7seg(d, x, 0, 7, DIGITS[num // 10], (255, 255, 255))
    draw_grid_7seg(d, x + 5, 0, 7, DIGITS[num % 10], (255, 255, 255))


def render_colon(d):
    draw_grid_Vseg(d, 11, 2, 7, 2, (255, 255, 255))
    draw_grid_Vseg(d, 11, 4, 7, 2, (255, 255, 255))


def render_text(d, text, blankidx=None):
    bs = bytearray(text)

    if blankidx is not None:
        bs[blankidx:blankidx + 1] = b'_'
    if MODE == DISPLAY:
        ltime = utime.localtime()
        wday = ltime[6]
        d.print(DAY_STRING[wday] + bs.decode(), fg=(128, 128, 128), bg=None, posx=5, posy=54)
    else:
        fg_color = (0, 255, 128) if MODE in (CHANGE_YEAR, CHANGE_MONTH, CHANGE_DAY) else (0, 128, 128)
        d.print(MODES[MODE], fg=fg_color, bg=None, posx=5, posy=54)


def render_bar(d, num):
    d.rect(5, 72, 0 + num * 2, 80, col=(int(255 // 52) * num, int(255 // 52) * num, int(255 // 52) * num))


def render(d):
    year, month, mday, hour, min, sec, wday, yday = utime.localtime()
    d.clear()
    ctrl_backlight(d)

    if MODE == CHANGE_YEAR:
        render_num(d, year // 100, 1)
        render_num(d, year % 100, 13)
    elif MODE == CHANGE_MONTH:
        render_num(d, month, 13)
    elif MODE == CHANGE_DAY:
        render_num(d, mday, 13)
    else:
        render_num(d, hour, 1)
        render_num(d, min, 13)

    if MODE not in (CHANGE_YEAR, CHANGE_MONTH, CHANGE_DAY) and sec % 2 == 0:
        render_colon(d)

    formatted_date = "{:02}.".format(mday) + MONTH_STRING[month - 1] + str(year)[2:]
    render_text(d, formatted_date, None)
    render_battery(d)
    render_bar(d, sec)

    d.update()


PREV_SECOND = 0


def render_every_second(display):
    t = utime.localtime()
    sec = t[5]
    global PREV_SECOND
    if PREV_SECOND < sec:
        render(display)
        if sec is 59:
            PREV_SECOND = -1
        else:
            PREV_SECOND += 1


BUTTON_SEL = 1 << 0
BUTTON_UP = 1 << 1
BUTTON_DOWN = 1 << 2
BUTTON_SEL_LONG = 1 << 3
BUTTON_UP_LONG = 1 << 4
BUTTON_DOWN_LONG = 1 << 5
pressed_prev = 0
button_sel_time = 0
button_up_time = 0
button_down_time = 0


def check_buttons():
    global pressed_prev, button_sel_time, button_up_time, button_down_time

    t = utime.time()
    pressed = buttons.read(buttons.BOTTOM_LEFT | buttons.TOP_RIGHT | buttons.BOTTOM_RIGHT)
    cur_buttons = 0

    if pressed & buttons.BOTTOM_LEFT and not pressed_prev & buttons.BOTTOM_LEFT:
        button_sel_time = t
    elif not pressed & buttons.BOTTOM_LEFT and pressed_prev & buttons.BOTTOM_LEFT:
        if button_sel_time < t:
            cur_buttons |= BUTTON_SEL_LONG
        else:
            cur_buttons |= BUTTON_SEL

    if pressed & buttons.TOP_RIGHT and not pressed_prev & buttons.TOP_RIGHT:
        button_sel_time = t
    elif not pressed & buttons.TOP_RIGHT and pressed_prev & buttons.TOP_RIGHT:
        if button_sel_time < t:
            cur_buttons |= BUTTON_UP_LONG
        else:
            cur_buttons |= BUTTON_UP

    if pressed & buttons.BOTTOM_RIGHT and not pressed_prev & buttons.BOTTOM_RIGHT:
        button_sel_time = t
    elif not pressed & buttons.BOTTOM_RIGHT and pressed_prev & buttons.BOTTOM_RIGHT:
        if button_sel_time < t:
            cur_buttons |= BUTTON_DOWN_LONG
        else:
            cur_buttons |= BUTTON_DOWN

    pressed_prev = pressed
    return cur_buttons


def modTime(yrs, mth, day, hrs, mns, sec):
    ltime = utime.localtime()
    new = utime.mktime(
        (ltime[0] + yrs, ltime[1] + mth, ltime[2] + day, ltime[3] + hrs, ltime[4] + mns, ltime[5] + sec, None, None))
    utime.set_time(new)


def ctrl_display(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = CHANGE_HOURS


def ctrl_chg_hrs(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_MINUTES
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(0, 0, 0, 1, 0, 0)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(0, 0, 0, -1, 0, 0)


def ctrl_chg_mns(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_SECONDS
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(0, 0, 0, 0, 1, 0)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(0, 0, 0, 0, -1, 0)


def ctrl_chg_sec(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_YEAR
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(0, 0, 0, 0, 0, 1)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(0, 0, 0, 0, 0, -1)


def ctrl_chg_yrs(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_MONTH
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(1, 0, 0, 0, 0, 0)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(-1, 0, 0, 0, 0, 0)


def ctrl_chg_mth(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_DAY
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(0, 1, 0, 0, 0, 0)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(0, -1, 0, 0, 0, 0)


def ctrl_chg_day(bs):
    global MODE
    if bs & BUTTON_SEL_LONG:
        MODE = DISPLAY
    if bs & BUTTON_SEL:
        MODE = CHANGE_HOURS
    if bs & BUTTON_UP or bs & BUTTON_UP_LONG:
        modTime(0, 0, 1, 0, 0, 0)
    if bs & BUTTON_DOWN or bs & BUTTON_DOWN_LONG:
        modTime(0, 0, -1, 0, 0, 0)


def ctrl_backlight(d):
    Y_ANGLE = -30
    Y_SPAN = 20 #+/- around angle
    Z_ANGLE = 0
    Z_SPAN =10  #+/- around angle
    RELIABLE_THRESHOLD = 2
    MOVEMENT_THRESHOLD = 2
    VIEW_TIMEOUT = 10    
    
    global viewing_state #can be viewing, not_viewing, timeout
    global viewing_event_start_time #start of viewing event   
    global last_y_angle #last angle watch was held at in timeout state

    samples = bhi.read()
    if samples:
        sample = samples[-1]
        if viewing_state == 'viewing':
            #adjust brightness
            light = light_sensor.get_reading()
            display_brightness = int(light // 4) if light >= 4 else 1
            display_brightness = 100 if light > 300 else display_brightness
            d.backlight(display_brightness)
            #check for state transistion            
            if (utime.time()-viewing_event_start_time) > VIEW_TIMEOUT:#display was on for too long
                viewing_state = 'timeout'#go to timeout
                last_y_angle = sample.y #remember angle we are currently held at
            elif (sample.status >= RELIABLE_THRESHOLD):#if orientation data is reliable
                if (sample.z < (Z_ANGLE - Z_SPAN)) or (sample.z > (Z_ANGLE + Z_SPAN)) or (sample.y < (Y_ANGLE - Y_SPAN)) or (sample.y > (Y_ANGLE + Y_SPAN)):#and we are outside of viewing angle
                    viewing_state = 'not_viewing'#leave viewing state, as display is not held at correct angle
        elif viewing_state == 'not_viewing':
            #switch display off
            display_brightness = 0
            d.backlight(display_brightness)
            #check for state transition
            if (sample.status < RELIABLE_THRESHOLD):#data is unreliable
                viewing_state = 'viewing'#switch display on to be safe
                viewing_event_start_time = utime.time()
            else:#data is reliable
                if (sample.z > (Z_ANGLE - Z_SPAN)) and (sample.z < (Z_ANGLE + Z_SPAN)) and (sample.y > (Y_ANGLE - Y_SPAN)) and (sample.y < (Y_ANGLE + Y_SPAN)):# we are inside viewing angle
                    viewing_state = 'viewing'#switch display on
                    viewing_event_start_time = utime.time()
        elif viewing_state == 'timeout':
            #switch display off
            display_brightness = 0
            d.backlight(display_brightness)
            #state transistions
            if (abs(sample.y-last_y_angle)>MOVEMENT_THRESHOLD):# there has been movement #removed(data is unreliable) because it leads to loop if unreliable all the time:(sample.status < RELIABLE_THRESHOLD)
                viewing_state = 'viewing'#switch display on 
                viewing_event_start_time = utime.time()   
            last_y_angle = sample.y #remember angle we are currently held at


# MODE values
DISPLAY = 0
CHANGE_HOURS = 1
CHANGE_MINUTES = 2
CHANGE_SECONDS = 3
CHANGE_YEAR = 4
CHANGE_MONTH = 5
CHANGE_DAY = 6

MODE = DISPLAY
MODES = {
    DISPLAY: '---',
    CHANGE_HOURS: '>-----HOURS',
    CHANGE_MINUTES: '>---MINUTES',
    CHANGE_SECONDS: '>---SECONDS',
    CHANGE_YEAR: '>------YEAR',
    CHANGE_MONTH: '>-----MONTH',
    CHANGE_DAY: '>-------DAY',
}

CTRL_FNS = {
    DISPLAY: ctrl_display,
    CHANGE_HOURS: ctrl_chg_hrs,
    CHANGE_MINUTES: ctrl_chg_mns,
    CHANGE_SECONDS: ctrl_chg_sec,
    CHANGE_YEAR: ctrl_chg_yrs,
    CHANGE_MONTH: ctrl_chg_mth,
    CHANGE_DAY: ctrl_chg_day,
}


def main():
    light_sensor.start()
    with display.open() as d:
        while True:
            bs = check_buttons()
            CTRL_FNS[MODE](bs)
            if MODE == DISPLAY:
                render(d)#update continously, TODO: check for current consumption increase
                #render_every_second(d)#update clock every second
            else:
                render(d)


main()
