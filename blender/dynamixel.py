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

def openSerial(path, baud=38400):
    uc = None
    try:
        uc = serial.Serial(path, baud)
    except:
        pass

    if uc and uc.isOpen():
        print('opened', uc.name)
        uc.write(b'plevel silent\n')
    else:
        print('Error:', path, 'not opened')

    return uc    

########################################################################
import ola
from ola.ClientWrapper import ClientWrapper

# Holds an array of 512 DMX channels.
# Channels go from 0-511 and have value 0-255.
# OLA can't individually address DMX channels, so this class only
# invokes the DMX subsystem if there has been a change
# To use, call set() on individual channels and then call send().
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
    
    # sends to OLA if there has been a change    
    def send(self):
        if not self.client or not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(1, self.data)
        
    # pass a start channel and any number of channel values
    # values are integers 0-255
    # you must call send to transmit the changes
    def set(self, channel, *values):
        #print('DMX.set channel', index, '=', values)
        for v in values:
            if self.data[channel] != v:
                self.data[channel] = v
                self.dataChanged = True
                channel += 1
                
    # pass a start channel and any number of channel values
    # values are numbers between 0 and 1
    # you must call send to transmit the changes
    def setFraction(self, channel, *values):
        intValues = tuple(int(255*v) for v in values)
        self.set(channel, *intValues)

    # sets all channels to 0 and transmits
    def off(self):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send()

    # convenience to set and transmit a list of values starting at channel 0
    def setAndSend(*values):
        i = 0
        for v in values:
            self.set(i, v)
            i += 1
        self.send()

DMX = DmxChannels()

########################################################################
# LED controller
ucLEDs = openSerial('/dev/led')

# arguments are PWM values 0-255
def setLEDs(*values):
    if ucLEDs == None: return

    cmd = 'leds'
    for v in values:
        cmd += ' ' + str(v)

    cmd += '\n'
    #print(cmd)
    ucLEDs.write(str.encode(cmd))

def setOneLEDInvFrac(intensity):
    # board takes intensity inverted
    chan1 = int(255 * (1.0 - intensity))
    setLEDs(chan1, 0, 0, 0, 0, 0)
    
########################################################################
# dynamixel servos
ucServos = openSerial('/dev/arbotix')

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
    scene = bge.logic.getCurrentScene()

    for o in scene.lights:
        if o.name.startswith('Spot'):
            #grab starting channel number from name
            channel = int(o.name[4:])
            intensity = o.energy
            rgb = o.color

            DMX.setFraction(channel, intensity, *rgb)#, 255)
            DMX.send()
            setOneLEDInvFrac(intensity)
            
        """elif o.name.startswith('LED'):
            channel = int(o.name[3:])
            intensity = o.energy
            setOneLEDInvFrac(channel, intensity)"""

            
    for o in scene.objects:
        if o.name.startswith('Servo'):
            pass

def k(cont):
    #ob = cont.owner
    #setOneLEDInvFrac(ob.energy)
    #d = bge.logic.getCurrentScene().lights
    #for i in d: print(i.energy)
    if keypressed(bge.events.ZKEY):
        DMX.off()
        bge.logic.endGame()
        return  #don't do anything else this frame!

    if keypressed(bge.events.QKEY): 
        setServoPos({3:512, 4:512})
        bge.logic.getCurrentScene().lights['Spot0'].energy = 0.0
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 0, 0]
    if keypressed(bge.events.WKEY):
        setServoPos({3:400, 4:400})
        bge.logic.getCurrentScene().lights['Spot0'].energy = 0.5
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 1.0, 0]
    if keypressed(bge.events.EKEY):
        setServoPos({3:300, 4:300})
        bge.logic.getCurrentScene().lights['Spot0'].energy = 1.0
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 0, 1.0]
        
    monitorScene()
    
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