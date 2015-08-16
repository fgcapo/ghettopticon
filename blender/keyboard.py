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
#arduino = serial.Serial('/dev/ttyACM2', 9600)
#arduino = serial.Serial('COM20', 115200)

Inc = .01
Servos = {}

class Servo:
    """
    - id is the servo ID for the uC
    - name is the blender bone name
    Angles are stored in blender space, in radians.
    Servos accept degrees.
    TODO clarify types of transformations between blender and servo space.
    """
    def __init__(self, id, name, axis, initial, min, max, servoNegate=False, servoFlip=False):
        self.id = id
        self.name = name
        self.axis = axis
        self.pos = initial
        self.min = min
        self.max = max
        self.servoNegate = servoNegate
        self.servoFlip = servoFlip
    
    def new(id, name, initial, axis, min, max, servoNegate=False, servoFlip=False):
        s = Servo(id, name, initial, axis, min, max, servoNegate, servoFlip)
        Servos[name] = s
    
    def increment(self, inc):
        self.move(self.pos + inc)
        
    def move(self, pos):
        pos = min(pos, self.max)
        pos = max(pos, self.min)
        self.pos = pos
        
        self.arduinoWrite()
        
        axis = self.axis
        if   (axis == 'x'): v = mathutils.Vector((pos, 0, 0))
        elif (axis == 'y'): v = mathutils.Vector((0, pos, 0))
        elif (axis == 'z'): v = mathutils.Vector((0, 0, pos))
        
        ob.channels[self.name].joint_rotation = v
        ob.update()
        return pos

    def arduinoWrite(self):
        degrees = int(self.pos * 180/pi)
        print(self.id, ':', degrees, ' degrees in blender space', sep='')
        
        if self.servoNegate: degrees = -degrees
        if self.servoFlip: degrees = 180 - degrees
        #if self.name == 'shoulder.L': degrees = 180 - (degrees + 90)
        #if self.name == 'shoulder.R': degrees = 180 - (degrees + 90)
        
        if arduino:
            arduino.write(struct.pack('>B', self.id))
            arduino.write(struct.pack('>B', degrees))
            arduino.write(struct.pack('>B', ord('\n')))

def incrementBone(name, inc):
    servo = Servos[name]
    servo.increment(inc)

##############################################################################
# servo joint definitions

#Left Arm
Servo.new(0,    'shoulder.L',      'y',    pi/2,   0,      pi)
Servo.new(1,    'upperarm.L',      'x',    0,      0,      pi,     servoNegate=True)
Servo.new(2,    'forearm.L',       'x',    0,      0,      pi,     servoFlip=True)
Servo.new(3,    'hand.L',          'y',    0,      0,      pi,     servoFlip=True)

#Right Arm
Servo.new(4,    'shoulder.R',      'y',    pi/2,   0,      pi)
Servo.new(5,    'upperarm.R',      'x',    0,     -pi,     0,      servoFlip=True, servoNegate=True)
Servo.new(6,    'forearm.R',       'x',    0,      0,      pi)
Servo.new(7,    'hand.R',          'y',    0,      0,      pi,     servoFlip=True)

#Head
Servo.new(8,    'neck',            'y',    0,      -pi,     0)
Servo.new(9,    'nod',             'x',    0,      0,       pi)
Servo.new(10,   'face',            'y',    0,      0,       pi)

# set initial positions in blender space
for name, servo in Servos.items(): servo.increment(0)

def k():
#Left Arm
    if keydown(bge.events.ONEKEY): angle = incrementBone('shoulder.L', Inc)
    if keydown(bge.events.TWOKEY): angle = incrementBone('shoulder.L', -Inc)

    if keydown(bge.events.QKEY): angle = incrementBone('upperarm.L', Inc)
    if keydown(bge.events.WKEY): angle = incrementBone('upperarm.L', -Inc)
        
    if keydown(bge.events.AKEY): angle = incrementBone('forearm.L', Inc)
    if keydown(bge.events.SKEY): angle = incrementBone('forearm.L', -Inc)

    if keydown(bge.events.ZKEY): angle = incrementBone('hand.L', Inc)
    if keydown(bge.events.XKEY): angle = incrementBone('hand.L', -Inc)
#Right Arm
    if keydown(bge.events.NINEKEY): angle = incrementBone('shoulder.R', Inc)
    if keydown(bge.events.ZEROKEY): angle = incrementBone('shoulder.R', -Inc)

    if keydown(bge.events.IKEY): angle = incrementBone('upperarm.R', Inc)
    if keydown(bge.events.OKEY): angle = incrementBone('upperarm.R', -Inc)
        
    if keydown(bge.events.JKEY): angle = incrementBone('forearm.R', Inc)
    if keydown(bge.events.KKEY): angle = incrementBone('forearm.R', -Inc)

    if keydown(bge.events.NKEY): angle = incrementBone('hand.R', Inc)
    if keydown(bge.events.MKEY): angle = incrementBone('hand.R', -Inc)
#Head
    if keydown(bge.events.THREEKEY): angle = incrementBone('neck', -Inc)
    if keydown(bge.events.FOURKEY): angle = incrementBone('neck', Inc)

    if keydown(bge.events.FIVEKEY): angle = incrementBone('nod', Inc)
    if keydown(bge.events.SIXKEY): angle = incrementBone('nod', -Inc)
        
    if keydown(bge.events.SEVENKEY): angle = incrementBone('face', Inc)
    if keydown(bge.events.EIGHTKEY): angle = incrementBone('face', -Inc)

