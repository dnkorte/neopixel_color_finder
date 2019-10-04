# neopixel_color_finder: use knobs to discover good colors and find their codes
# 
# MIT License
# 
# Copyright (c) 2019 Don Korte
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 

"""
neopixel_color_finder: use knobs to discover good colors and find their codes
===========================================================

Author(s):  Don Korte
Repository: https://github.com/dnkorte/neopixel_color_finder

notes: use neopixel jewel as display; "vertical" column of 3 show current value
from sliders; the 4 "outriggers" to side show the 4 saved values;   
use a 4-button matrix to save the 4 values - press and hold saves the current
value from sliders into that "slot"; quick press displays the saved value on 
the TFT and all 7 leds; motion on any "knob" causes it to revert back to
displaying the knob-requested value.

this version uses TFT display, and requires an M4 class ItsyBitsy
must create lib/ folder and install the following Adafruit libraries:
    adafruit_display_text (folder)
    adafruit_display_shapes (folder)
    adafruit_st7735r.mpy
    adafruit_debouncer.mpy
    neopixel.mpy
    simplieio.mpy

ItsyBitsy pin connections:
    to NeoPixel: 5!
    to TFT (1.8in TFT http://www.adafruit.com/products/358):
        SCK /   SCK
        MOSI /  MOSI
        10:     CS
        9:      Reset
        7:      DC
        (Note also TFT requires power, ground, and backlight)
        (Note also ItsyBitsy requires Vbat and Gnd, and it also supplies power for PB pullup (Vhi))
    to pushbutton: 11  (normally pulled high, press takes it low)
"""

import board
import time
import simpleio
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
import displayio
import terminalio
from adafruit_st7735r import ST7735R
from adafruit_display_text import label
from adafruit_display_shapes.circle import Circle
from adafruit_debouncer import Debouncer
import neopixel

def display_val_r(text):
    disp_r_textbox.text = text
    _, _, textwidth, _ = disp_r_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (15 - (textwidth/2)))
    text_group_r.x = new_x

def display_val_g(text):
    disp_g_textbox.text = text
    _, _, textwidth, _ = disp_g_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (40 - (textwidth/2)))
    text_group_g.x = new_x

def display_val_b(text):
    disp_b_textbox.text = text
    _, _, textwidth, _ = disp_b_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (65 - (textwidth/2)))
    text_group_b.x = new_x

def display_val_h(text):
    line_h_textbox.text = text
    _, _, textwidth, _ = line_h_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (40 - (textwidth/2)))
    text_group_h.x = new_x

def get_voltage(pin):
    avg = 0
    num_readings = 5
    for _ in range(num_readings):
        avg += pin.value        
    avg /= num_readings
    analog_volts = avg * (pin.reference_voltage / 65536) 
    return analog_volts

def get_knob(pin):
    avg = 0
    num_readings = 8
    for _ in range(num_readings):
        this_value = simpleio.map_range(pin.value, 1000, 64000, 0, 255)
        avg += this_value                
    avg /= num_readings
    return int(avg)

# setup for NeoPixels (RGB) ########################################################
# NeoPixel "strip" (of 2 individual LEDS Adafruit 1938) connected on D5
NUMPIXELS = 2
ORDER = neopixel.RGB
neopixels = neopixel.NeoPixel(board.D5, NUMPIXELS, brightness=0.2, auto_write=False, pixel_order=ORDER)

# setup a/d converters for knobs
analog_R_pin = AnalogIn(board.A0)
analog_G_pin = AnalogIn(board.A1)
analog_B_pin = AnalogIn(board.A2)

# color definitions for TFT display
D_RED = 0xFF0000
D_GREEN = 0x00FF00
D_BLUE1 = 0x0000FF
D_BLUE = 0x7480ff
D_YELLOW = 0xFFFF00
D_ORANGE = 0xFF8000
D_BLACK = 0x000000
D_WHITE = 0xFFFFFF

# setup ST7735 display 1.8in TFT http://www.adafruit.com/products/358 ###############
# see https://github.com/adafruit/Adafruit_CircuitPython_ST7735R/blob/master/examples/st7735r_128x160_simpletest.py
spi = board.SPI()
tft_cs = board.D10
tft_dc = board.D7

displayio.release_displays()
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D9)

display = ST7735R(display_bus, width=160, height=128, rotation=90, bgr=True)

# Make the display context
splash = displayio.Group(max_size=10)
display.show(splash)

big_circle = Circle(80, 22, 20, fill=D_BLACK, outline=D_WHITE)
splash.append(big_circle)

circle_saved_1 = Circle(20, 58, 10, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_saved_1)
circle_saved_2 = Circle(60, 58, 10, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_saved_2)
circle_saved_3 = Circle(100, 58, 10, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_saved_3)
circle_saved_4 = Circle(140, 58, 10, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_saved_4)

text = ""
text_group_r = displayio.Group(max_size=2, scale=2, x=5, y=86)
disp_r_textbox = label.Label(terminalio.FONT, text=text, color=D_RED, max_glyphs=12)
text_group_r.append(disp_r_textbox) 
splash.append(text_group_r)

text_group_g = displayio.Group(max_size=2, scale=2, x=55, y=86)
disp_g_textbox = label.Label(terminalio.FONT, text=text, color=D_GREEN, max_glyphs=12)
text_group_g.append(disp_g_textbox) 
splash.append(text_group_g)

text_group_b = displayio.Group(max_size=2, scale=2, x=105, y=86)
disp_b_textbox = label.Label(terminalio.FONT, text=text, color=D_BLUE, max_glyphs=12)
text_group_b.append(disp_b_textbox) 
splash.append(text_group_b)

text_group_h = displayio.Group(max_size=2, scale=2, x=0, y=112)
line_h_textbox = label.Label(terminalio.FONT, text=text, color=D_YELLOW, max_glyphs=12)
text_group_h.append(line_h_textbox) 
splash.append(text_group_h)

# text_group3 = displayio.Group(max_size=2, scale=3, x=72, y=56)
# text_group3 = displayio.Group(max_size=2, scale=2, x=0, y=118)
# line3_textbox = label.Label(terminalio.FONT, text=text, color=D_YELLOW, max_glyphs=12)
# text_group3.append(line3_textbox) 
# splash.append(text_group3)


# setup environment #################################################################

# Built in red LED
led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

# Digital input with pullup on D7
button = DigitalInOut(board.D11)
button.direction = Direction.INPUT
button.pull = Pull.UP
debounced_button = Debouncer(button)

fastloop_counter = 0

while True:
    # check_button()
    debounced_button.update()
    if debounced_button.fell:
        pass

    time.sleep(0.01)
    fastloop_counter += 1
    if fastloop_counter > 24:
        fastloop_counter = 0
    else:
        continue

    led.value = not debounced_button.value

    R_knob = get_knob(analog_R_pin)
    #R_led_val = int(R_bits/255)
    # R_led_val = R_bits
    display_val_r(str(R_knob))

    G_knob = get_knob(analog_G_pin)
    # G_led_val = int(G_bits/255)
    display_val_g(str(G_knob))

    B_knob = get_knob(analog_B_pin)
    # B_led_val = int(B_bits/255)
    display_val_b(str(B_knob))

    rgb_value = (R_knob << 16) | (G_knob << 8) | B_knob
    display_val_h(hex(rgb_value))

    neopixels[0] = (R_knob, G_knob, B_knob)
    neopixels[1] = (R_knob, G_knob, B_knob)
    neopixels.show()

    big_circle.fill = rgb_value