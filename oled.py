import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

#i2c_RST
RST = 4
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_address=0x3C)

disp.begin()
disp.clear()
disp.display()

# create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)

padding = -2
top = padding
bottom = height-padding
startPos = 2
pos = startPos

font = ImageFont.load_default()
#font = ImageFont.truetype('/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf', 8)

#cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
#CPU = subprocess.check_output(cmd, shell = True )
#cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
#MemUsage = subprocess.check_output(cmd, shell = True )
cmd = "hostname -I | cut -d\' \' -f1"
IP = subprocess.check_output(cmd, shell = True )
cmd = "date"
_date = (subprocess.check_output(cmd, shell = True )).split()
date = ""

for i in range(len(_date)):
    if (i != 0) and (i != 4):
        date = date + (_date[i]).strip() + " "

print("OLED date: " + date)

t1 = 'Server started at'
t1max, t1unused = draw.textsize(t1, font=font)
t1 = t1 + ' '*((width-(t1max+startPos))/6) + t1

t2 = date
t2max, t2unused = draw.textsize(t2, font=font)
t2 = t2 + ' '*((width-(t2max+startPos))/6) + t2

t3 = 'IP: ' + IP.strip()
t3max, t3unused = draw.textsize(t3, font=font)
t3 = t3 + ' '*((width-(t3max+startPos))/6) + t3

t4 = '-->'*3
t4max, t4unused = draw.textsize(t4, font=font)
t4 = t4 + ' '*((width-(t4max+startPos))/6) + t4

def oled_system():
    global pos, startPos
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    x = pos
    draw.text((x, top), t1, font=font, fill=255)
    draw.text((x, top+8), t2, font=font, fill=255)
    draw.text((x, top+16), t3, font=font, fill=255)
    draw.text((x, top+24), t4,  font=font, fill=255)
    pos = pos - 2
    if pos < -width+startPos*2:
        pos = startPos
    disp.image(image)
    disp.display()

def oled_printMsg(_msg=['', '']):
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((startPos, top), "TOPIC:", font=font, fill=255)
    draw.text((startPos, top + 8), "=" + _msg[0], font=font, fill=255)
    draw.text((startPos, top + 16), "PAYLOAD:" , font=font, fill=255)
    draw.text((startPos, top + 24), "=" + _msg[1], font=font, fill=255)
    disp.image(image)
    disp.display()

def oled_clear():
    # Clear image buffer by drawing a black filled box.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    disp.image(image)
    disp.display()
