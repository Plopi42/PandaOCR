#! /usr/bin/python

#
# This script is an example of what should not be done while generating Captcha
#

import sys
import string
import random

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


def generateText(size=8, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for x in range(size))

def createImage(width, height):
    return Image.new("RGB", (width, height), "grey")

def saveImage(im, filename):
    im.save(filename, "PNG")

def writeText(im, text, position, fontname, fontsize, color):
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(fontname, fontsize)
    draw.text(position, text, color, font=font)

def writeTextRandomly(im, text, fontname, fontsize, color):
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(fontname, fontsize)

    width  = im.size[0]
    middleHeight = (im.size[1] - fontsize) / 2

    step = (width - 20) / len(text)
    i    = 10
    j    = 15
    for c in text:
        draw.text((i, middleHeight + j), c, color, font=font)
        i += step
        j  = -j

def writeTextCell(im, text, fontname, fontsize, color):
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(fontname, fontsize)

    width  = im.size[0]
    middleHeight = (im.size[1] - fontsize) / 2

    step = (width - 2) / len(text)
    i    = 0
    for c in text:
        draw.text((i + 3, middleHeight), c, color, font=font)
        i += step

def harderCaptcha(im):
    writeTextRandomly(im, text, "eufm10.ttf", 36, (42, 42, 0))

def simpleCaptcha(im):
    writeTextCell(im, text, "DejaVuSans-Bold.ttf", 24, (42, 42, 0))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Error: Not enough parameters !"
        print "Usage: %s <1|2> <generatedfilename> [<captchatext>]" % sys.argv[0]
        sys.exit(2)

    im   = createImage(240, 80)

    text = ""
    if len(sys.argv) > 3:
        text = sys.argv[3][0:8]
    else:
        text = generateText()
        print "Generated: %s" % text

    if sys.argv[1] == "1":
        simpleCaptcha(im)
    else:
        harderCaptcha(im)

    saveImage(im, sys.argv[2])
