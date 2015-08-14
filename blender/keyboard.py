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
arduino = serial.Serial('/dev/ttyACM0', 9600)
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
        if self.name == 'shoulder': degrees = 180 - (degrees + 90)
        
        if arduino:
            arduino.write(struct.pack('>B', self.id))
            arduino.write(struct.pack('>B', degrees))
            arduino.write(struct.pack('>B', ord('\n')))


Servo.new(0, 'shoulder',    0,    -pi/2,      pi/2)
Servo.new(1, 'upperarm',    0,     -pi,    0,      servoNegate=True)
Servo.new(2, 'forearm',     0,     0,      pi,     servoFlip=True)


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
moveBoneServo('shoulder', 0, 'y', 0)
moveBoneServo('upperarm', 1, 'x', 0)
moveBoneServo('forearm',  2, 'x', 0)

def k():

    if keydown(bge.events.QKEY): angle = moveBoneServo('shoulder', 0, 'y', Inc)
    if keydown(bge.events.WKEY): angle = moveBoneServo('shoulder', 0, 'y', -Inc)

    if keydown(bge.events.AKEY): angle = moveBoneServo('upperarm', 1, 'x', Inc)
    if keydown(bge.events.SKEY): angle = moveBoneServo('upperarm', 1, 'x', -Inc)
        
    if keydown(bge.events.ZKEY): angle = moveBoneServo('forearm', 2, 'x', Inc)
    if keydown(bge.events.XKEY): angle = moveBoneServo('forearm', 2, 'x', -Inc)