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
    to NeoPixel Jewel: 5!       (power this from ItsyBitsy Vhi)
    to TFT (1.8in TFT http://www.adafruit.com/products/358):
        SCK /   SCK
        MOSI /  MOSI
        10:     CS
        9:      Reset
        7:      DC
        A0:     analog RED
        A1:     analog GREEN
        A2:     analog BLUE
        12:     Pushbutton 3 active low
        11:     Pushbutton 1 active low
        1:      Pushbutton 4 active low
        0:      Pushbutton 2 active low
        (Note also TFT requires power, ground, and backlight)
        (Note also ItsyBitsy requires Vbat and Gnd, and it also supplies power for PB pullup (3v))
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

# setup for NeoPixels (RGB) ########################################################
# NeoPixel "strip" (of 2 individual LEDS Adafruit 1938) connected on D5
NUMPIXELS = 7
ORDER = neopixel.GRB
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

# startup mode displays rainbow cycle until a knob is changed ====================================
# 
# note when exporting BMP file from Gimp, compatibility options should be "no color space info", 
# and advance options may be  "16 bit R5 G6 B5"
f = open("/splash2.bmp", "rb")
background = displayio.OnDiskBitmap(f)
face = displayio.TileGrid(background, pixel_shader=displayio.ColorConverter(), x=0, y=0)
splash.append(face)
R_knob_last = get_knob(analog_R_pin)
G_knob_last = get_knob(analog_G_pin)
B_knob_last = get_knob(analog_B_pin)
for j in range(5000):
    for i in range(NUMPIXELS):
        pixel_index = (i * 256 // NUMPIXELS) + j*10
        neopixels[i] = wheel(pixel_index & 255)
    neopixels.show()
    time.sleep(0.05)
    R_knob = get_knob(analog_R_pin)
    G_knob = get_knob(analog_G_pin)
    B_knob = get_knob(analog_B_pin)
    if (abs(R_knob - R_knob_last) > 5) or (abs(G_knob - G_knob_last) > 5) or (abs(B_knob - B_knob_last) > 5):
        break
    R_knob_last = R_knob
    G_knob_last = G_knob
    B_knob_last = B_knob

# user is ready, so turn off all the neopixels and blank the screen
for i in range(NUMPIXELS):      
    neopixels[i] = (0, 0, 0)
    neopixels.show()

splash.pop()    # undisplay the opening graphic

# end of startup splash mode ======================================================================



big_circle = Circle(80, 36, 25, fill=D_BLACK, outline=D_WHITE)
splash.append(big_circle)

circle_mem_1 = Circle(35, 12, 12, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_mem_1)
circle_mem_2 = Circle(35, 60, 12, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_mem_2)
circle_mem_3 = Circle(125, 12, 12, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_mem_3)
circle_mem_4 = Circle(125, 60, 12, fill=D_BLACK, outline=D_WHITE)
splash.append(circle_mem_4)

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

# pushbutton for mem cell 1 (yellow wire button 1 on PyGRRL)
button1 = DigitalInOut(board.D11)
button1.direction = Direction.INPUT
button1.pull = Pull.UP
debounced_button1 = Debouncer(button1)

# pushbutton for mem cell 2 (green wire button 2 on PyGRRL)
button2 = DigitalInOut(board.D0)
button2.direction = Direction.INPUT
button2.pull = Pull.UP
debounced_button2 = Debouncer(button2)

# pushbutton for mem cell 3 (purple wire button 3 on PyGRRL)
button3 = DigitalInOut(board.D12)
button3.direction = Direction.INPUT
button3.pull = Pull.UP
debounced_button3 = Debouncer(button3)

# pushbutton for mem cell 4 (blue wire button 4 on PyGRRL)
button4 = DigitalInOut(board.D1)
button4.direction = Direction.INPUT
button4.pull = Pull.UP
debounced_button4 = Debouncer(button4)

fastloop_counter = 0
mode = "show_knob_value"
mem1_rgb = (0, 0, 0)
mem2_rgb = (0, 0, 0)
mem3_rgb = (0, 0, 0)
mem4_rgb = (0, 0, 0)
keep_this_rgb = 0
btn1_start_time = 0
btn2_start_time  = 0
btn3_start_time  = 0
btn4_start_time  = 0
btn1_status = "waiting"
btn2_status = "waiting"
btn3_status = "waiting"
btn4_status = "waiting"
knob_r_prior_disp_saved_mode = 0
knob_g_prior_disp_saved_mode = 0
knob_b_prior_disp_saved_mode = 0



while True:
    # check_button()
    debounced_button1.update()
    debounced_button2.update()
    debounced_button3.update()
    debounced_button4.update()

    if debounced_button1.fell:
        btn1_start_time = time.monotonic()
        circle_mem_1.outline =  D_YELLOW
    if debounced_button2.fell:
        btn2_start_time = time.monotonic()
        circle_mem_2.outline =  D_YELLOW
    if debounced_button3.fell:
        btn3_start_time = time.monotonic()
        circle_mem_3.outline =  D_YELLOW
    if debounced_button4.fell:
        btn4_start_time = time.monotonic()
        circle_mem_4.outline =  D_YELLOW

    if debounced_button1.rose:
        downtime = time.monotonic() - btn1_start_time
        circle_mem_1.outline =  D_WHITE
        if (downtime < 0.75):
            btn1_status = "short"
        else:
            btn1_status = "long"

    if debounced_button2.rose:
        downtime = time.monotonic() - btn2_start_time        
        circle_mem_2.outline =  D_WHITE
        if (downtime < 0.75):
            btn2_status = "short"
        else:
            btn2_status = "long"

    if debounced_button3.rose:
        downtime = time.monotonic() - btn3_start_time       
        circle_mem_3.outline =  D_WHITE
        if (downtime < 0.75):
            btn3_status = "short"
        else:
            btn3_status = "long"

    if debounced_button4.rose:
        downtime = time.monotonic() - btn4_start_time       
        circle_mem_4.outline =  D_WHITE
        if (downtime < 0.75):
            btn4_status = "short"
        else:
            btn4_status = "long"

    time.sleep(0.01)

    fastloop_counter += 1

    if fastloop_counter > 24:  

        # every 0.25 seconds we read knobs and update displays
        fastloop_counter = 0  
        R_knob = get_knob(analog_R_pin)
        G_knob = get_knob(analog_G_pin)
        B_knob = get_knob(analog_B_pin)

        if (mode == "show_knob_value"):
            rgb_value_i = (R_knob << 16) | (G_knob << 8) | B_knob
            keep_this_rgb = (R_knob, G_knob, B_knob)
            display_val_r(str(R_knob))
            display_val_g(str(G_knob))
            display_val_b(str(B_knob))
            display_val_h(hex(rgb_value_i))

            neopixels[0] = (R_knob, G_knob, B_knob)
            neopixels[1] = (R_knob, G_knob, B_knob)
            neopixels[4] = (R_knob, G_knob, B_knob)
            neopixels.show()

            big_circle.fill = rgb_value_i

            if btn1_status == "long":
                mem1_rgb = keep_this_rgb
                circle_mem_1.fill = rgb_value_i
                neopixels[6] = (R_knob, G_knob, B_knob)     # upper left
                btn1_status = "waiting"

            if btn2_status == "long":
                mem2_rgb = keep_this_rgb
                circle_mem_2.fill = rgb_value_i
                neopixels[5] = (R_knob, G_knob, B_knob)     # lower left
                btn2_status = "waiting"

            if btn3_status == "long":
                mem3_rgb = keep_this_rgb
                circle_mem_3.fill = rgb_value_i
                neopixels[2] = (R_knob, G_knob, B_knob)     # upper right
                btn3_status = "waiting"

            if btn4_status == "long":
                mem4_rgb = keep_this_rgb
                circle_mem_4.fill = rgb_value_i
                neopixels[3] = (R_knob, G_knob, B_knob)     # lower right
                btn4_status = "waiting"


            if btn1_status == "short":
                print("button 1 short")
                btn1_status = "waiting"
                # mode == "showing_stored_value"

            if btn2_status == "short":
                print("button 2 short")
                btn2_status = "waiting"
                # mode == "showing_stored_value"

            if btn3_status == "short":
                print("button 3 short")
                btn3_status = "waiting"
                # mode == "showing_stored_value"

            if btn4_status == "short":
                print("button 4 short")
                btn4_status = "waiting"
                # mode == "showing_stored_value"
        else:
            # here we are in show_memory_value mode
            pass
        