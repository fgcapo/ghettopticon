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
ucChair = None
#ucChair = serial.Serial('/dev/ttyACM0', 9600)
#ucChair = serial.Serial('COM23', 9600)

if ucChair and ucChair.isOpen():
    print('opened ', ucChair.name)
else:
    print("ucChair not opened")

# arguments are letter, integer (signed byte)
def sendChairCmd(cmd, val=0):
    #print(cmd)
    if ucChair == None: return
    ucChair.write(struct.pack('>B', ord(cmd)))
    ucChair.write(struct.pack('>b', val))
    ucChair.write(struct.pack('>B', ord('\n')))

#########################################################################

def k():
    # heartbeat character sent every frame;
    # uC will stop motion if this is not received after a short amount of time
    sendChairCmd('~')

    if keydown(bge.events.EKEY): sendChairCmd('e')
    if keydown(bge.events.DKEY): sendChairCmd('d')
    if keydown(bge.events.UKEY): sendChairCmd('u')
    if keydown(bge.events.HKEY): sendChairCmd('h')
    if keydown(bge.events.SPACEKEY): sendChairCmd(' ')


mousePos = [0, 0]
mouseSensitivity = .1
 
def m(cont):
    ob = cont.owner
    mouse = cont.sensors["Mouse"]
    
    h = render.getWindowHeight()//2
    w = render.getWindowWidth()//2
    
    mouseDelta = [
        (mouse.position[0] - w) * mouseSensitivity,
        (h - mouse.position[1]) * mouseSensitivity]

    render.setMousePosition(w, h)

    mousePos[0] += mouseDelta[0]
    mousePos[1] += mouseDelta[1]

    ob.localPosition.x = mousePos[0]
    ob.localPosition.y = mousePos[1]

    print(mousePos)

    #rotate 45 degrees to motor impulses
    motorPos = [
        mousePos[0]*pi/2 - mousePos[1]*pi/2,
        mousePos[1]*pi/2 + mousePos[0]*pi/2,
    ]

    #send new motor positions to uC
    sendChairCmd('R', int(motorPos[0]))
    sendChairCmd('L', int(motorPos[1]))