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

notes: use neopixel jewel as display; vertical column of 3 show current value
from sliders; the 4 "outriggers" to side show the 4 saved values;   
use a 4-button matrix to save the 4 values - press and hold saves the current
value from sliders into that "slot"; quick press displays the saved value on 
the TFT and all 7 leds, until clicked again (or a different one is clicked); 
once quick-clicked on the displayed value it returns to slider control

this version uses TFT display, and requires an M4 class ItsyBitsy
must create lib/ folder and install the following Adafruit libraries:
    adafruit_display_text (folder)
    adafruit_display_shapes (folder)
    adafruit_st7735r.mpy
    adafruit_debouncer.mpy
    neopixel.mpy

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
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
import displayio
import terminalio
from adafruit_st7735r import ST7735R
from adafruit_display_text import label
from adafruit_display_shapes.circle import Circle
from adafruit_debouncer import Debouncer
import neopixel

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def display_line1(text):
    line1_textbox.text = text
    _, _, textwidth, _ = line1_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (40 - (textwidth/2)))
    text_group1.x = new_x

def display_line2(text):
    line2_textbox.text = text
    _, _, textwidth, _ = line2_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (40 - (textwidth/2)))
    text_group2.x = new_x

def display_line3(text):
    line3_textbox.text = text
    _, _, textwidth, _ = line3_textbox.bounding_box
    # note this field is scaled by 2 so we initially center it in a 80 pixel space
    new_x = int(2 * (40 - (textwidth/2)))
    text_group3.x = new_x

def get_voltage(pin):
    avg = 0
    num_readings = 5
    for _ in range(num_readings):
        avg += pin.value        
    avg /= num_readings
    analog_volts = avg * (pin.reference_voltage / 65536) 
    return analog_volts

def get_analog_bits(pin):
    avg = 0
    num_readings = 5
    for _ in range(num_readings):
        avg += pin.value        
    avg /= num_readings
    return avg

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
D_BLUE = 0x0000FF
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

left_circle = Circle(40, 30, 15, fill=D_RED)
splash.append(left_circle)
right_circle = Circle(120, 30, 15, fill=D_RED)
splash.append(right_circle)

text = ""
text_group1 = displayio.Group(max_size=2, scale=2, x=0, y=72)
line1_textbox = label.Label(terminalio.FONT, text=text, color=D_YELLOW, max_glyphs=12)
text_group1.append(line1_textbox) 
splash.append(text_group1)

text_group2 = displayio.Group(max_size=2, scale=2, x=0, y=96)
line2_textbox = label.Label(terminalio.FONT, text=text, color=D_YELLOW, max_glyphs=12)
text_group2.append(line2_textbox) 
splash.append(text_group2)

# text_group3 = displayio.Group(max_size=2, scale=3, x=72, y=56)
text_group3 = displayio.Group(max_size=2, scale=2, x=0, y=118)
line3_textbox = label.Label(terminalio.FONT, text=text, color=D_YELLOW, max_glyphs=12)
text_group3.append(line3_textbox) 
splash.append(text_group3)


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

display_line1("Line 1")
display_line2("Line 2")
display_line3("Line 3")

while True:
    # check_button()
    debounced_button.update()
    if debounced_button.fell:
        pass

    time.sleep(0.01)
    fastloop_counter += 1
    if fastloop_counter > 9:
        fastloop_counter = 0
    else:
        continue

    led.value = not debounced_button.value

    R_bits = get_analog_bits(analog_R_pin)
    R_led_val = int(R_bits/256)

    G_bits = get_analog_bits(analog_G_pin)
    G_led_val = int(G_bits/256)
    display_line2(str(G_led_val))

    B_bits = get_analog_bits(analog_B_pin)
    B_led_val = int(B_bits/256)

    rgb_value = (R_led_val << 16) | (G_led_val << 8) | B_led_val

    display_line1("R:"+str(R_led_val)+" G:"+str(G_led_val))
    display_line2("B:"+str(B_led_val))

    display_line3(hex(rgb_value))

    neopixels[0] = (R_led_val, G_led_val, B_led_val)
    neopixels[1] = (R_led_val, G_led_val, B_led_val)
    neopixels.show()