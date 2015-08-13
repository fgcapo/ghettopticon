import mathutils
import bge
from math import pi
import serial
import struct

# Just shortening names here
keyboard = bge.logic.keyboard
JUST_ACTIVATED = bge.logic.KX_INPUT_JUST_ACTIVATED

ob = bge.logic.getCurrentController().owner

Inc = .1
servoAngles = {0:0, 1:0, 2:0}
"""
arduino = serial.Serial('/dev/ttyACM0', 115200)

def moveBoneServo(name, servo, axis, inc):
    global servoAngles
    
    servoAngles[servo] += inc
    
    if (axis == 0): v = mathutils.Vector((servoAngles[servo], 0, 0))
    if (axis == 1): v = mathutils.Vector((0, servoAngles[servo], 0))
    if (axis == 2): v = mathutils.Vector((0, 0, servoAngles[servo]))
    #v[axis] = servoAngles[servo]
    
    ob.channels[name].joint_rotation = v
    ob.update()    
    return servoAngles[servo]


def arduinoWrite(servo, radians):
    degrees = int(radians * 180 / pi)
    #arduino.write(struct.pack('>B', servo))
    #arduino.write(struct.pack('>B', degrees))
    #arduino.write(struct.pack('>B', ord('\n')))
    #print(angle, end=" ")

def k():
    global inc, servoAngles, ob
    
    if keyboard.events[bge.events.QKEY] == JUST_ACTIVATED:
        #angle = moveBoneServo('shoulder', 0, 1, Inc)
        #arduinoWrite(0, angle)        
        #servoAngles[servo] += inc
        ob = bge.logic.getCurrentController().owner
        ob.channels['shoulder'].joint_rotation = mathutils.Vector([0, 1, 0])
       
    if keyboard.events[bge.events.WKEY] == JUST_ACTIVATED:
        angle = moveBoneServo('shoulder', 0, 1, -Inc)
        arduinoWrite(0, angle)

    if keyboard.events[bge.events.AKEY] == JUST_ACTIVATED:
        angle = moveBoneServo('upperarm', 1, 0, Inc)
        arduinoWrite(1, angle)        
        
    if keyboard.events[bge.events.SKEY] == JUST_ACTIVATED:
        angle = moveBoneServo('upperarm', 1, 0, -Inc)
        arduinoWrite(1, angle)

    if keyboard.events[bge.events.ZKEY] == JUST_ACTIVATED:
        angle = moveBoneServo('forearm', 2, 0, Inc)
        arduinoWrite(2, angle)        
        
    if keyboard.events[bge.events.XKEY] == JUST_ACTIVATED:
        angle = moveBoneServo('forearm', 2, 0, -Inc)
        arduinoWrite(2, angle)
"""
x=0
def k():
 global x
# Get the whole bge scene
 #scene = bge.logic.getCurrentScene()
# Helper vars for convenience
 #source = scene.objects

# Get the whole Armature
 #main_arm = so`urce.get('Armature')
 ob = bge.logic.getCurrentController().owner

 ob.channels['forearm'].joint_rotation = mathutils.Vector([0,0,x])
 ob.channels['shoulder'].joint_rotation = mathutils.Vector([0,x,0])
 ob.channels['upperarm'].joint_rotation = mathutils.Vector([x,0,0,])
 ob.update()

 x=x+.01