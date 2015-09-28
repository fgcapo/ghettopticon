import bge
from bge import render
import math
from math import *
import mathutils
import serial
import struct

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

########################################################################
uc = serial.Serial('/dev/ttyUSB0', 9600)
#uc = serial.Serial('COM23', 9600)

if uc and uc.isOpen():
    print('opened ', uc.name)
else:
    print("uc not opened")

# arguments are letter, integer (signed byte)
def setServoPos(anglesDict):
    if uc == None: return

    cmd = 's'
    for id,angle in anglesDict.items():
        cmd += ' ' + str(id) + ':' + str(angle)

    cmd += '\n'
    uc.write(str.encode(cmd))

#########################################################################
def k(cont):

    if keydown(bge.events.QKEY): setServoPos({1:300})
    if keydown(bge.events.WKEY): setServoPos({1:500})
    if keydown(bge.events.EKEY): setServoPos({1:700})
    
# mouse tracking subroutine for interactive wheelchair movement
# This routine maps mouse position to wheelchair velocity, which was the simplest way I could think of
#  to control the chair. I believe mapping the mouse position to the chair position would require
#  mathematical integration plus some planning, as the chair can only move forward and back.
#
# Moving the mouse forward from the starting location increases forward speed.
# Moving backward from starting location increases backward speed.
# Moving left or right of the starting location makes the char spin in place (?)
# All other mouse positions are interpolations of the above, ex: forward-right makes a left turn
#  (can invert this easily).
# 
# Use spacebar to stop. 
# TODO test mouse after hitting spacebar
def m(cont):
    global mousePos, mouseSensitivity
    ob = cont.owner
    mouse = cont.sensors["Mouse"]
    
    # calculate the amount mouse cursor moved from the center since last frame
    mouseDelta = [
        (mouse.position[0] - centerX) * mouseSensitivity,
        (centerY - mouse.position[1]) * mouseSensitivity]

    # move mouse cursor back to center
    render.setMousePosition(centerX, centerY)

    # update our secret internal mouse position
    mousePos[0] += mouseDelta[0]
    mousePos[1] += mouseDelta[1]

    # move cube onscreen
    ob.localPosition.x = mousePos[0]
    ob.localPosition.y = mousePos[1]

    # rotate 45 degrees to convert to motor impulses
    motorPos = [
        -mousePos[0]*cos45 + mousePos[1]*cos45,
        (mousePos[0]*cos45 + mousePos[1]*cos45),
    ]

    print(mousePos)

    # send new motor positions to uC
    # NO LONGER SUPPORTED
    #sendChairCmd('R', int(motorPos[0]))
    #sendChairCmd('L', int(motorPos[1]))