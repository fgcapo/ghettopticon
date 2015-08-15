import bge
import math
from math import *
import mathutils
import serial
import struct

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_ACTIVE

ob = bge.logic.getCurrentController().owner

arduino = None
arduino = serial.Serial('/dev/ttyACM2', 9600)
#arduino = serial.Serial('COM20', 115200)

Inc = .01
Servos = {}

class Servo:
    """
    - id is the servo ID for the uC
    - name is the blender bone name
    Angles are stored in blender space, and in radians.
    Servos accept degrees.
    TODO clarify types of transformations between blender and servo space.
    """
    def __init__(self, id, name, initial, min, max, servoNegate=False, servoFlip=False):
        self.id = id
        self.name = name
        self.pos = initial
        self.min = min
        self.max = max
        self.servoNegate = servoNegate
        self.servoFlip = servoFlip
    
    def new(id, name, initial, min, max, servoNegate=False, servoFlip=False):
        Servos[id] = Servo(id, name, initial, min, max, servoNegate, servoFlip)
        #Servos[id].arduinoWrite()   # move to initial position

    def arduinoWrite(self):
        degrees = int(self.pos * 180/pi)
        print(self.id, ':', degrees, ' degrees in blender space', sep='')
        
        if self.servoNegate: degrees = -degrees
        if self.servoFlip: degrees = 180 - degrees
        if self.name == 'shoulder.L': degrees = 180 - (degrees + 90)
        if self.name == 'shoulder.R': degrees = 180 - (degrees + 90)
        
        if arduino:
            arduino.write(struct.pack('>B', self.id))
            arduino.write(struct.pack('>B', degrees))
            arduino.write(struct.pack('>B', ord('\n')))

#Left Arm
Servo.new(0, 'shoulder.L',    0,    -pi/2,      pi/2)
Servo.new(1, 'upperarm.L',    0,     -pi,    0,      servoNegate=True)
Servo.new(2, 'forearm.L',     0,     0,      pi,     servoFlip=True)
#Right Arm
Servo.new(3, 'shoulder.R',    0,    -pi/2,      pi/2)
Servo.new(4, 'upperarm.R',    0,     -pi,    0,      servoFlip=True, servoNegate=True)
Servo.new(5, 'forearm.R',     0,     0,      pi,     )


def moveBoneServo(name, id, axis, inc):
    servo = Servos[id]
    #if servo.invert: inc = -inc
    
    pos = servo.pos + inc
    pos = min(pos, servo.max)
    pos = max(pos, servo.min)
    servo.pos = pos
    
    servo.arduinoWrite()
    
    if (axis == 'x'): v = mathutils.Vector((pos, 0, 0))
    if (axis == 'y'): v = mathutils.Vector((0, pos, 0))
    if (axis == 'z'): v = mathutils.Vector((0, 0, pos))
    
    ob.channels[name].joint_rotation = v
    ob.update()
    return pos

# set initial positions in blender space
#Left Arm
moveBoneServo('shoulder.L', 0, 'y', 0)
moveBoneServo('upperarm.L', 1, 'x', 0)
moveBoneServo('forearm.L',  2, 'x', 0)
#Right Arm
moveBoneServo('shoulder.R', 3, 'y', 0)
moveBoneServo('upperarm.R', 4, 'x', 0)
moveBoneServo('forearm.R',  5, 'x', 0)

def k():

#Left Arm
    if keydown(bge.events.QKEY): angle = moveBoneServo('shoulder.L', 0, 'y', Inc)
    if keydown(bge.events.WKEY): angle = moveBoneServo('shoulder.L', 0, 'y', -Inc)

    if keydown(bge.events.AKEY): angle = moveBoneServo('upperarm.L', 1, 'x', Inc)
    if keydown(bge.events.SKEY): angle = moveBoneServo('upperarm.L', 1, 'x', -Inc)
        
    if keydown(bge.events.ZKEY): angle = moveBoneServo('forearm.L', 2, 'x', Inc)
    if keydown(bge.events.XKEY): angle = moveBoneServo('forearm.L', 2, 'x', -Inc)
#Right Arm
    if keydown(bge.events.OKEY): angle = moveBoneServo('shoulder.R', 3, 'y', Inc)
    if keydown(bge.events.PKEY): angle = moveBoneServo('shoulder.R', 3, 'y', -Inc)

    if keydown(bge.events.KKEY): angle = moveBoneServo('upperarm.R', 4, 'x', Inc)
    if keydown(bge.events.LKEY): angle =    moveBoneServo('upperarm.R', 4, 'x', -Inc)
        
    if keydown(bge.events.NKEY): angle = moveBoneServo('forearm.R', 5, 'x', Inc)
    if keydown(bge.events.MKEY): angle = moveBoneServo('forearm.R', 5, 'x', -Inc)