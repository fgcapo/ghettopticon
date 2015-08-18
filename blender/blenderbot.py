import bge
from bge import render
import math
from math import *
import mathutils
import serial
import struct

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

cont = bge.logic.getCurrentController()
ob = cont.owner

########################################################################
arduino = None
arduino = serial.Serial('/dev/ttyACM0', 9600)
#arduino = serial.Serial('COM23', 9600)

if arduino and arduino.isOpen():
    print(arduino.name)
else:
    print("arduino not opened")

def sendArduinoByte(val):
    if arduino == None: return
    arduino.write(struct.pack('>B', ord(val)))

# arguments are letter, integer
def sendArduinoCmd(cmd, val=0):
    if arduino == None: return
    arduino.write(struct.pack('>B', ord(cmd)))
    arduino.write(struct.pack('>B', val))
    arduino.write(struct.pack('>B', ord('\n')))

#########################################################################

def k():
    # heartbeat character sent every frame;
    # uC will stop motion if this is not received in time
    sendArduinoByte('~')

    if keydown(bge.events.EKEY):
        sendArduinoCmd('e')
        #ob.localPosition.x = 10
        #ob.localPosition.y = 10

    if keydown(bge.events.DKEY): sendArduinoCmd('d')
    if keydown(bge.events.UKEY): sendArduinoCmd('u')
    if keydown(bge.events.HKEY): sendArduinoCmd('h')
    if keydown(bge.events.SPACEKEY): sendArduinoCmd(' ')


mousePos = [0, 0]

#set speed for camera movement
sensitivity = .1
 
def m():
    mouse = cont.sensors["Mouse"]
    
    h = render.getWindowHeight()//2
    w = render.getWindowWidth()//2
    
    mouseDelta = [
        (mouse.position[0] - w) * sensitivity,
        (h - mouse.position[1]) * sensitivity]

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
    sendArduinoCmd('R', int(motorPos[0]))
    sendArduinoCmd('L', int(motorPos[1]))