#     Copyright (c) 2020 Guido Kraemer
#     Copyright (c) 2018 Jouko Strömmer
#     Copyright (c) 2017 Waveshare
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PIL import Image

from papertty.drivers.drivers_base import GPIO
from papertty.drivers.drivers_consts import EPD4in2v2const
from papertty.drivers.drivers_partial import WavesharePartial

# The driver works as follows:
#
# This driver is for the following display:
#     400x300, 4.2inch E-Ink display module v2
#     SKU: 13353
#     Part Number: 4.2inch e-Paper Module
#     Brand: Waveshare
#     UPC: 614961950887
#
# When rotating the display with side of the connector of the display (not the
# module) at the bottom, the display width is 400 and the height is 300. The
# letters on the module and the connector of the module point to the right.
#
# The origin of the display is in the top left corner and filling happens by
# line.
#
# The frame buffer is an array of bytes of size 400 * 300 / 8, each bit is one
# pixel 0 is white, 1 is black
#
# The framebuffer should always contain the entire image, redrawing happens
# only on the changed area.
#
# The properties width and height of the incoming image correspond to the
# properties of the display, access to the pixels of the image is:
# image.load[width, height]


class EPD4in2v2(WavesharePartial, EPD4in2v2const):
    """WaveShare 4.2" """

    # code adapted from  epd_4in2.c
    # https://github.com/waveshare/e-paper/blob/8973995e53cb78bac6d1f8a66c2d398c18392f71/raspberrypi%26jetsonnano/c/lib/e-paper/epd_4in2.c

    # note: this works differently (at least in the c code): there is a memory
    # buffer, the same size as the display. we partially refresh the memory
    # buffer with the image at a position and the do self.partial_refresh with
    # the entire memory buffer and the area to be refreshed.

    # note: this code is outside of drivers_partial.py because the class has to
    # override many methdos and therefore is way to long

    def __init__(self):
        super(WavesharePartial, self).__init__(name='4.2"',
                                               width=400,
                                               height=300)
        self.supports_partial = True

        # this is the memory buffer that will be updated!
        self.frame_buffer = [0xff] * (self.width * self.height // 8)

    # TODO: universal?
    def set_setting(self, command, data):
        print(f"set_setting")
        self.send_command(command)
        self.send_data(data)

    # TODO: universal?
    def set_resolution(self):
        print(f"set_resolution")
        self.set_setting(self.RESOLUTION_SETTING,
                         [(self.width >> 8) & 0xff,
                          self.width & 0xff,
                          (self.height >> 8) & 0xff,
                          self.height & 0xff])

    def reset(self):
        print(f"reset")
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(100)
        self.digital_write(self.RST_PIN, GPIO.LOW)
        self.delay_ms(2)
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(100)

    def send_command(self, command):
        self.digital_write(self.DC_PIN, GPIO.LOW)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        self.spi_transfer([command])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    def send_data(self, data):
        self.digital_write(self.DC_PIN, GPIO.HIGH)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        if type(data) == list:
            for d in data:
                self.spi_transfer([d])
        else:
            self.spi_transfer([data])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    # ReadBusy
    def wait_until_idle(self):
        print(f"wait_until_idle")
        #self.send_command(self.GET_STATUS)
        while self.digital_read(self.BUSY_PIN) == 1:
            print(f"busy, waiting")
            self.delay_ms(20) #20
            #self.send_command(self.GET_STATUS)
            #self.delay_ms(100)

    def turn_on_display(self):
        print(f"turn_on_display")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xF7)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_fast(self):
        print(f"turn_on_display_fast")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_partial(self):
        print(f"turn_on_display_partial")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xFF)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()
        
    def turn_on_display_4gray(self):
        print(f"turn_on_display_4gray")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xCF)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def init(self, partial=True, gray=False, **kwargs):
        print(f"init")
        self.partial_refresh = partial
        self.gray = gray

        if self.epd_init() != 0:
            return -1

        self.reset()
        self.wait_until_idle()

        self.send_command(0x12) #SWRESET
        self.wait_until_idle()

        self.send_command(0x21)  # Display update control
        self.send_data(0x40)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)

        self.send_command(0x11)  # data  entry  mode
        self.send_data(0x03)  # X-mode

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.wait_until_idle()

        self.clear()

    def init_fast(self, partial=True, gray=False, **kwargs):
        print(f"init_fast")
        self.partial_refresh = partial
        self.gray = gray

        if self.epd_init() != 0:
            return -1

        self.reset()
        self.wait_until_idle()

        self.send_command(0x12) #SWRESET
        self.wait_until_idle()

        self.send_command(0x21)  # Display update control
        self.send_data(0x40)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)

        self.send_command(0x1A)
        self.send_data(0x5A)  

        self.send_command(0x22)  # Load temperature value
        self.send_data(0x91)  
        self.send_command(0x20)  
        self.wait_until_idle()

        self.send_command(0x11)  # data  entry  mode
        self.send_data(0x03)  # X-mode

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.wait_until_idle()

    def clear(self):
        print(f"clear")
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        self.send_data([0xff] * int(self.height * linewidth))

        self.send_command(0x26)
        self.send_data([0xff] * int(self.height * linewidth))

        self.turn_on_display()

    # Writing outside the range of the display will cause an error.
    def fill(self, color, fillsize):
        print(f"fill: color {color}, fillsize {fillsize}")
        """Slow fill routine"""

        div, rem = divmod(self.height, fillsize)
        image = Image.new('1', (self.width, fillsize), color)

        for i in range(div):
            self.draw(0, i * fillsize, image)

        if rem != 0:
            image = Image.new('1', (self.width, rem), color)
            self.draw(0, div * fillsize, image)

    def display_full(self):
        print(f"display_full")
        self.send_command(0x24)
        self.send_data(self.frame_buffer)

        self.send_command(0x26)
        self.send_data(self.frame_buffer)

        self.turn_on_display()

    def display_partial(self):
        print(f"display partial")
 
        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00) 

        self.send_command(0x24) # WRITE_RAM

        self.send_data(self.frame_buffer)  
        self.turn_on_display_partial()


    def sleep(self):
        print(f"sleep")
        """Put the display in deep sleep mode"""
        self.send_command(0x10)  # DEEP_SLEEP
        self.send_data(0x01)


    def frame_buffer_to_image(self):
        print(f"frame_buffer_to_image")
        """Returns self.frame_buffer as a PIL.Image"""

        im = Image.new('1', (self.width, self.height), "white")
        pi = im.load()

        for j in range(self.height):
            idxj = j * self.width // 8
            for i in range(self.width):
                idiv, irem = divmod(i, 8)
                mask = 0b10000000 >> irem
                idxi = idiv
                pi[i, j] = self.frame_buffer[idxi + idxj] & mask

        return im

    def set_frame_buffer(self, x, y, image):
        print(f"set_frame_buffer, {x}, {y}, {image}")
        """Updates self.frame_buffer with image at (x, y)"""

        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        print(f"running loop on image of size {imwidth}x{imheight}")

        for j in range(imheight):
            idxj = (y + j) * self.width // 8
            for i in range(imwidth):
                idiv, irem = divmod(x + i, 8)
                mask = 0b10000000 >> irem
                idxi = idiv

                if pixels[i, j] != 0:
                    self.frame_buffer[idxi + idxj] |= mask
                else:
                    self.frame_buffer[idxi + idxj] &= ~mask

    def draw(self, x, y, image):
        print(f"draw, x:{x}, y;{y}, image:{image}")
        """replace a particular area on the display with an image"""

        self.set_frame_buffer(x, y, image)

        if self.partial_refresh:
            self.display_partial()
        else:
            self.display_full()
