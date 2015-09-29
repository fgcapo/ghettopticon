import bpy
import bge
from bge import render
import math
from math import *
import mathutils
import serial
import struct


def keypressed(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

########################################################################
import ola
from ola.ClientWrapper import ClientWrapper

# OLA can't individually address DMX channels, so only do a send
# if a channel value changes
class DmxChannels:
    def __init__(self):
        self.data = bytearray(512)
        self.dataChanged = False
        self.client = None
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
        except:
            print("Error: couldn't connect to OLA server")
            
    def len():
        return len(self.data);
    
    def send(self):
        if not self.client or not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(1, self.data)
        
    # you must call send to tramist the changes
    def set(self, index, value):
        #print('DMX.set', index, value)
        if self.data[index] != value:
            self.data[index] = value
            self.dataChanged = True

    def setFromStart(*values):
        i = 0
        for v in values:
            self.set(i, v)
            i += 1
        self.send()

    def off(self):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send()

DMX = DmxChannels()

########################################################################
# LED controller
ucLEDs = None
try:
    ucLEDs = serial.Serial('/dev/led', 9600)
except:
    pass

if ucLEDs and ucLEDs.isOpen():
    print('opened ', ucLEDs.name)
else:
    print("Error: ucLEDs not opened")

# arguments are PWM values 0-255
def setLEDs(*values):
    if ucLEDs == None: return

    cmd = 'leds'
    for v in values:
        cmd += ' ' + str(v)

    cmd += '\n'
    #print(cmd)
    ucLEDs.write(str.encode(cmd))
    
########################################################################
# dynamixel servos
ucServos = None
try:
    ucServos = serial.Serial('/dev/arbotix', 9600)
except:
    pass

if ucServos and ucServos.isOpen():
    print('opened ', ucServos.name)
else:
    print("Error: ucServos not opened")

# argument is a dictionary of id:angle
# angles are 0-1023; center is 512; safe angle range is 200-824
def setServoPos(anglesDict):
    if ucServos == None: return

    cmd = 's'
    for id,angle in anglesDict.items():
        cmd += ' ' + str(id) + ':' + str(angle)

    cmd += '\n'
    #print(cmd)
    ucServos.write(str.encode(cmd))

#########################################################################
def monitorScene():
    for o in bpy.data.objects:
        if o.name.startswith('Spot'):
            rgb = o.data.color
            DMX.set(0, int(255*o.data.energy))
            DMX.set(1, int(255*rgb[0]))
            DMX.set(2, int(255*rgb[1]))
            DMX.set(3, int(255*rgb[2]))
            #DMX.set(4, 255) #white light
            #DMX.set(0, 255)
            DMX.send()
        elif o.name.startswith('Servo'):
            pass

def k(cont):
    if keypressed(bge.events.ZKEY):
        DMX.off()
        bge.logic.endGame()
        return  #don't do anything else this frame!

    if keypressed(bge.events.QKEY): 
        setServoPos({3:512, 4:512})
        setLEDs(0, 0, 0, 0)
        DMX.off()
    if keypressed(bge.events.WKEY):
        setServoPos({3:400, 4:400})
        setLEDs(100, 100, 100, 100)
        DMX.setAndSend(255, 0, 255, 0, 0)
    if keypressed(bge.events.EKEY):
        setServoPos({3:300, 4:300})
        setLEDs(255, 255, 255, 255)
        DMX.setAndSend(255, 0, 0, 255, 0)
        
    #monitorScene()
    
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