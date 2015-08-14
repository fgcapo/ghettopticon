import bge
import math
from math import *
import mathutils
import serial

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_ACTIVE

ob = bge.logic.getCurrentController().owner

arduino = None#serial.Serial('/dev/ttyACM0', 115200)

Inc = .1
Servos = {}

class Servo:
    """angles are stored in radians but converted to degrees when sent to uC"""
    def __init__(self, id, initial, min, max):
        self.id = id
        self.pos = initial
        self.min = min
        self.max = max
    
    def new(id, initial, min, max):
        Servos[id] = Servo(id, initial, min, max)

    def arduinoWrite(self):
        degrees = int(self.pos * 180/pi)
        print(degrees, end=" ")
        if arduino:
            arduino.write(struct.pack('>B', self.id))
            arduino.write(struct.pack('>B', degrees))
            arduino.write(struct.pack('>B', ord('\n')))

Servo.new(0, 0, 0, pi)
Servo.new(1, 0, 0, pi)
Servo.new(2, 0, 0, pi)

def moveBoneServo(name, id, axis, inc):
    servo = Servos[id]
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


def k():
    if keydown(bge.events.QKEY):
        angle = moveBoneServo('shoulder', 0, 'y', Inc)   
       
    if keydown(bge.events.WKEY):
        angle = moveBoneServo('shoulder', 0, 'y', -Inc)

    if keydown(bge.events.AKEY):
        angle = moveBoneServo('upperarm', 1, 'z', Inc)    
        
    if keydown(bge.events.SKEY):
        angle = moveBoneServo('upperarm', 1, 'z', -Inc)
        
    if keydown(bge.events.ZKEY):
        angle = moveBoneServo('forearm', 2, 'z', Inc)   
        
    if keydown(bge.events.XKEY):
        angle = moveBoneServo('forearm', 2, 'z', -Inc)

