import serial
import struct
import threading
import time

NumArrays = 4

# returns a blocking read object
def openSerial(path, baud=38400):
    uc = None
    try:
        uc = serial.Serial(path, baud)
    except:
        pass

    if uc and uc.isOpen():
        print('opened', uc.name)
        #print(uc.readline())
        #uc.write(b'plevel silent\n')
    else:
        print('Error:', path, 'not opened')

    return uc

# Creates a thread that handles reading lines from serial without blocking the calling
# thread. Override handleLine, which will be called from this object's thread.
class SerialThread (threading.Thread):
    def __init__(self, path, baud=38400, timeout=50, delim='\n'):
        self.readPeriod = .01   # seconds
        self.delim = str.encode(delim)
        self.uc = None
        self.shouldExit = False
        try:
            # don't bother doing any other initialization if we can't open the port
            self.uc = serial.Serial(path, baud)
            self.lock = threading.Lock()
            threading.Thread.__init__(self)
            self.start()
        except:
            pass

        if self.uc and self.uc.isOpen():
            print('opened', self.uc.name)
        else:
            print('Error:', path, 'not opened')
          
    def valid(self):
        return self.uc and not self.shouldExit
        
    def exit(self):
        self.shouldExit = True
    
    def write(self, data):
        if not self.valid(): return
        self.lock.acquire()
        self.uc.write(data)
        self.lock.release()

    # override this
    def handleLine(self, line):
        print('override me!', line)

    def run(self):
        b = bytearray()
        
        while self.valid():
            #print('run')
            time.sleep(self.readPeriod)
            self.lock.acquire()
            num = self.uc.inWaiting()
            if num:
                b += self.uc.read(num)
                #print(len(b))
            self.lock.release()
            
            #TODO find all newlines
            ixNewline = b.find(self.delim)
            while ixNewline != -1:
                v = b[:ixNewline].decode("utf-8")
                self.handleLine(v)
                b = b[ixNewline+1:]
                ixNewline = b.find(self.delim)
                
        if self.uc:
            self.uc.close()
            self.uc = None

########################################################################
# LED controller
class LEDs(SerialThread):
    def __init__(self, path):
        SerialThread.__init__(self, path)        
        self.MinValue = 0
        self.MaxValue = 255
        self.NumChannels = NumArrays
        self.values = [self.MinValue] * self.NumChannels

    def __str__(self):
      return str(self.values)

    def handleLine(self, line):
        #print(line)
        return

    def get(self, channel): return self.values[channel]

    # arguments are PWM values 0-255
    def set(self, channel, values):
      if isinstance(values, int): values = [values]
    
      for v in values:
        self.values[channel] = v
        channel += 1

      cmd = 'pwm'
      for v in self.values: cmd += ' ' + str(v)
      cmd += '\n'

      self.write(str.encode(cmd))

    #def setOneLEDInvFrac(intensity):
        # board takes intensity inverted
        #chan1 = int(255 * (1.0 - intensity))
        #setLEDs(chan1)
        
########################################################################
# dynamixel servos
class Servos(SerialThread):
    def __init__(self, path):
        SerialThread.__init__(self, path)
        self.mode = None
        self.numLinesToFollow = 0
        self.anglesDict = {}

        #self.NumServos = 4 * NumArrays
        #for i in range(1, self.NumServos+1):
        #    self.set(i, 512)

    def get(self, id): return self.anglesDict[id]

    def set(self, idOrDict, angle=None):
      if isinstance(idOrDict, int): self.anglesDict[idOrDict] = angle
      elif isinstance(idOrDict, dict): self.anglesDict = idOrDict
      else: raise BaseException('bad argument to Servos.setAngle')
      self.setServoPos()

    def __str__(self): return str(self.anglesDict)

    def handleLine(self, line):
        # read the positions of all servos, which is spread over multiple lines
        # expect the next some number of lines to be servo info
        if line.startswith('Servo Readings:'):
            self.numLinesToFollow = int(line[15:])
            self.mode = 'r'
            self.anglesDict = {}
            print('expecting', self.numLinesToFollow, 'servo readings')

        # information about a single servo, on a single line
        elif self.mode == 'r':
            id, pos = None, None
            for pair in line.split():
                kv = pair.split(':')
                key = kv[0]
                if   key == 'ID':  id = int(kv[1])
                elif key == 'pos': pos = int(kv[1])
            self.anglesDict[id] = pos
            self.numLinesToFollow -= 1
            
            # done, reset mode
            if self.numLinesToFollow == 0:
                print(self.anglesDict)
                self.mode = None
                
        #else: print(line)

    # argument is a dictionary of id:angle
    # angles are 0-1023; center is 512; safe angle range is 200-824
    def setServoPos(self, binary=False):
        if not self.valid(): return

        # send a text command which says to expect a block of binary
        # then send the angles as an array of 16-bit ints in order
        # angle is set to 0 for missing IDs
        if binary:
            maxID = 0  # IDs start at 1, so numAngles = highest ID
            for id,angle in anglesDict.items(): 
                maxID = max(maxID, id)

            cmd = 'B ' + str(maxID) + '\n'
            #print(cmd)
            self.write(str.encode(cmd))

            buf = bytearray()
            for id in range(1, maxID+1):
                angle = 0
                if id in anglesDict: angle = anglesDict[id]
                
                # 16-bit little endian
                buf += struct.pack('<H', angle)
            
            print(buf)
            ucServos.write(buf)

        # text protocol of id:angle pairs
        else:
            cmd = 's'
            for id,angle in self.anglesDict.items():
                cmd += ' ' + str(id) + ':' + str(angle)

            cmd += '\n'
            #print(cmd)
            self.write(str.encode(cmd))

    # takes one or a list of IDs
    # relaxes all if IDs is None
    def relax(self, IDs):
      if isinstance(IDs, int): IDs = [IDs]
      elif IDs is None: IDs = self.anglesDict.keys()

      cmd = 'relax'
      for id in IDs: cmd += ' ' + str(id)
      print(cmd)
      cmd += '\n'
      self.write(str.encode(cmd))

    def moveAllServos(self, pos, binary=False):
        anglesDict = {}
        for i in range(numServos):
            anglesDict[i+1] = pos
        self.setServoPos(binary)

    def readServos(self):
        self.write(b'r\n')

#ucServos = Servos('/dev/arbotix')

