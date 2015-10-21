import sys, os, os.path, threading, ast, time
from getch import getch
from ola.ClientWrapper import ClientWrapper
import microcontrollers as uc

ucServos = uc.Servos('/dev/arbotix')
ucLEDs = uc.LEDs('/dev/led')

"""class OlaThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.universe = 1
    self.lastDataSent = [0] * 512   # set from both send() and receive callback, so may have thread issues
    self.lastDataReceived = None

  def run(self):
    def onData(data):
        # TODO check on status before assigning data
        self.lastDataReceived = data
        #print(data)

    self.wrapper = ClientWrapper()
    self.client = self.wrapper.Client()
    self.client.RegisterUniverse(self.universe, self.client.REGISTER, onData)
    print('running OLA thread...')
    self.wrapper.Run()
    # TODO catch exceptions

  def exit(self):
    self.wrapper.Stop()

  def getLastReceived(self):
    return self.lastDataReceived

  def getLastSent(self):
    return self.lastDataSent

  def send(self, data):
    self.lastDataSent = data
    self.client.SendDmx(self.universe, data)

OLA = OlaThread()
OLA.start()"""

# Holds an array of 512 DMX channels.
# Channels go from 0-511 and have value 0-255.
# OLA can't individually address DMX channels, so this class only
# invokes the DMX subsystem if there has been a change
# To use, call set() on individual channels and then call send().
class DmxChannels:
    def __init__(self):
        self.NumChannels = 512
        self.MinValue = 0
        self.MaxValue = 255
        self.data = bytearray(self.NumChannels)
        
        self.dataChanged = False
        self.client = None
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
        except:
            print("Error: couldn't connect to OLA server")
            
    def exit(self):
      pass

    def get(self, index=None):
        if index is not None: return self.data[index]
        else: return list(self.data)
    
    # sends to OLA if there has been a change    
    def send(self):
        if not self.client or not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(1, self.data)
        
    # pass a start channel and any number of channel values
    # values are integers 0-255
    # you must call send to transmit the changes
    # can say set([values]), set(index, value) or set(index, [values])
    def set(self, channel, values=None):
        if values is None:
          values = channel
          channel = 0

        if isinstance(values, int): values = [values]
        #print('DMX.set channel', index, '=', values)
        for v in values:
            if self.data[channel] != v:
                self.data[channel] = v
                self.dataChanged = True
            channel += 1
                
    # pass a start channel and any number of channel values
    # values are numbers between 0 and 1
    # you must call send to transmit the changes
    def setFraction(self, channel, values=None):
        if values is None:
          values = channel
          channel = 0

        if isinstance(values, int) or isintance(values, float): values = [values]
        intValues = tuple(round(255*v) for v in values)
        self.set(channel, intValues)

    # sets all channels to 0 and transmits
    def off(self):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send()

    # convenience to set and transmit a list of values starting at channel 0
    def setAndSend(self, channel, values=None):
        self.set(channel, values)
        self.send()

DMX = DmxChannels()


def frange(start, end=None, inc=None):
    "A range function, that does accept float increments..."

    if end == None:
        end = start + 0.0
        start = 0.0
    else: start += 0.0 # force it to be a float

    if inc == None:
        inc = 1.0

    count = int((end - start) / inc)
    if start + count * inc != end:
        # need to adjust the count.
        # AFAIKT, it always comes up one short.
        count += 1

    L = [None,] * count
    for i in range(count):
        L[i] = start + i * inc

    return L

def restAfterWord(word, line):
  return line[line.find(word) + len(word):].strip()

def openCueFile(filenameOnly, mode='r'):
  return open('scenes/' + filenameOnly, mode)

########################################################
# cue commands

class Cue:
  def __init__(self, line):
    self.line = line

  def run(self, immediate=False):
    print('empty cue')

class CueSequence(Cue):
  def __init__(self, line):
    Cue.__init__(self, line)
    self.cues = []
  def add(self, cue):
    self.cues.append(cue)
  def run(self, immediate=False):
    for cue in self.cues:
      print ('-', cue.line.strip())
      cue.run()

# return a dictionary of DMX, LED channels, and Servo angles
def loadCueFile(filenameOnly):
  try:
    with openCueFile(filenameOnly) as f:
      firstLine = f.readline()

      # test for file version
      if firstLine[0] == '[':
        # just a list of dmx channel values
        dmx = ast.literal_eval(firstLine)
        return {'DMX':dmx}

      json = ast.literal_eval(firstLine)
      return
      # TODO check version
      """if json['version'] == 0:
        DMX.set(json['DMX'])
        ucLEDS.set(json['LightArm']['LEDs'])
        ucServos.set(json['LightArm']['Servos'])
      else:
        print('Error file version unknown')"""

  except BaseException as e:
    print(e)
    print('Hit SPACE to continue')
    getch()

# load scene from local file
class CueLoad(Cue):
  def __init__(self, line):
    Cue.__init__(self, line)

    tokens = line.split()
    if len(tokens) < 2:
      raise BaseException('no filename')

    filename = restAfterWord(tokens[0], line)
    #print(filename)
    try:
      self.target = loadCueFile(filename)
    except OSError as e:
      raise BaseException('Error loading file: ' + str(e))

  def run(self, immediate=False):
    #try:
      current = DMX.get()
      target = self.target['DMX']

      # allow for value of -1 to not change current value
      for i in range(len(current)):
        if target[i] >= 0: current[i] = target[i]

      DMX.set(0, current)

      # Light Arms
      ucLEDS.set(self.target['LightArm']['LEDs'])
      ucServos.set(self.target['LightArm']['Servos'])
      
    #except:
    #  raise BaseException('Error talking to OLA DMX server')

    
  # fade from current scene to new scene
  # usage:
  # fade <optional time in seconds> <filename>
class CueFade(Cue):
  def __init__(self, line):
    Cue.__init__(self, line)

    tokens = line.split()
    if len(tokens) < 2:
      raise BaseException('usage: fade <optional time in seconds> <filename>')

    try: 
      tok = tokens[1]
      self.period = float(tok)
      filename = restAfterWord(tok, line)
    except:
      self.period = 5.0
      filename = restAfterWord(tokens[0], line)

    try:      
      with openCueFile(filename) as f:
        text = f.readline()
        #print(text)
        self.target = ast.literal_eval(text)
    except (OSError, IOError) as e:
      raise BaseException('Error loading file: ' + str(e))
 
  def run(self, immediate=False):
    try:
      timestep = .05
      printPeriodPeriod = .25
      printPeriodTimestepCount = printPeriodPeriod / timestep

      current = DMX.get()
      vel = [0] * len(current)

      if immediate:
        OLA.send(self.target)
        return

      # calculate delta for each timestep
      # -1 means don't change
      for i in range(len(self.target)):
        if self.target[i] >= 0:
          vel[i] = (self.target[i] - current[i]) * (timestep / self.period)

      print('                 fading for', self.period, 'seconds..', end='', flush=True)

      # calculate new channel values, transmit and sleep
      for t in frange(0, self.period, timestep):
        for i in range(len(current)): current[i] += vel[i]
        channels = [int(x) for x in current] 
        DMX.setAndSend(0, channels)
        if t % printPeriodPeriod == 0: print('.', end='', flush=True)
        time.sleep(timestep)

      print('DONE')
    except:
      raise BaseException('Error talking to OLA DMX server')
    # TODO other exceptions having to do with the fade math


# instantiate a class and run it
def cmdCue(line, CueClass):
  try:
    cue = CueClass(line)
    cue.run()
  except BaseException as e:
    print(e)

# save current OLA scene
def cmdSave(tokens, line):
  if len(tokens) < 2:
    raise BaseException('no filename')

  filename = restAfterWord(tokens[0], line)
  dmx = str(DMX.get())
  #lightArm = "{\n 'version': 0\n 'DMX': " + dmx + ",\n 'LightArm': {\n  'Servos': " + str(ucServos) + ",\n  'LEDs': " + str(ucLEDs) + "\n }\n}"
  lightArm = "{'version': 0, 'DMX': " + dmx + ", 'LightArm': {'Servos': " + str(ucServos) + ", 'LEDs': " + str(ucLEDs) + "}}"
  
  #print(data)
#  try:
  with openCueFile(filename, 'w') as f:
      f.write(lightArm)
      f.write('\n')
#  except:
#    raise BaseException('Error saving file')

############################################################################3
# DMX slider data

def clearScreen():
    #os.system('clear')
    #print("\x1b[2J\x1b[H", end='')
    return

def fitServoRange(v): return max(212, min(812, v))
def fitLEDRange(v): return max(0, min(255, v))

class LightArmView:
  def __init__(self):
    self.lineInputKey = 'c'

    # ID of base servo; will they all be the same dimension?
    # other servo will be ID+1
    self.armIDs = [19, 25, 27, 29, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    self.PageWidth = 4    
    self.ixCursor = 0
    
    self.mode = 0   # index into self.Modes

  # modify one arm or a group of 4 at a time
  Modes = ['individual', 'group']

  def toggleMode(self):
    self.mode = (self.mode + 1 ) % len(self.Modes)
  def inSingleMode(self):
    return self.mode == 0

  # retrieve angle based on arm index on screen
  # type must be 'x' or 'y'
  def getAngle(self, type, index=None):
    if index is None: index = self.ixCursor
    id = self.armIDs[index]
    if type == 'y': id += 1
    elif type != 'x': raise BaiseException('bad dimension')
    return ucServos.get(id)

  # returns a list of the selected indices
  def selected(self):
    if self.inSingleMode():
      return [self.ixCursor]
    else:
      return range(self.group(), self.PageWidth)
     

  def idsGroupX(self):
      return map(lambda x: self.armIDs[x], self.selected()) 

  def idsGroupY(self):
      return map(lambda x: 1 + self.armIDs[x], self.selected())

   # add increment to the angle of the X servo of the currently selected arm(s)
  def modX(self, inc):
    ids = map(lambda x: self.armIDs[x], self.selected())
    for id in ids:
      ucServos.set(id, fitServoRange(ucServos.get(id) + inc))

  # add increment to the angle of the X servo of the currently selected arm(s)
  def modY(self, inc):
    ids = map(lambda x: 1 + self.armIDs[x], self.selected())
    for id in ids:
      ucServos.set(id, fitServoRange(ucServos.get(id) + inc))

  def modI(self, inc):
    channel = self.ixCursor // self.PageWidth
    ucLEDs.set(channel, fitLEDRange(ucLEDs.get(channel) + inc))

  def handleLineInput(self, line):
    tokens = line.split()
    if len(tokens) == 0: return
    cmd = tokens[0]

  def handleChar(self, ch): 
    ch = ch.lower()
    if ch == 'x':
      self.toggleMode() 
    if ch == '0':
      for i in self.selected():
        ucServos.set(self.armIDs[i], 512)
        ucServos.set(1 + self.armIDs[i], 512)
      #self.modX(512-self.getAngle('x'))
      #self.modY(512-self.getAngle('y'))
    elif ch == 'w':
      self.modY(1)
    elif ch == 's':
      self.modY(-1)
    elif ch == 'd':
      self.modX(1)
    elif ch == 'a':
      self.modX(-1)
    elif ch == 'q':
      self.modI(1)
    elif ch == 'e':
      self.modI(-1)

    elif ch == '\x1b':
      seq = getch() + getch()
      if seq == '[C': # left arrow
        if self.inSingleMode(): self.ixCursor += 1
        else: self.ixCursor = self.ixCursor - self.ixCursor % self.PageWidth + self.PageWidth
        self.ixCursor = min(len(self.armIDs)-1, self.ixCursor)
      elif seq == '[D': # right arrow
        if self.inSingleMode(): self.ixCursor -= 1
        else: self.ixCursor = self.ixCursor - self.ixCursor % self.PageWidth - self.PageWidth
        self.ixCursor = max(0, self.ixCursor)
      elif seq == '[A': pass # up arrow
      elif seq == '[B': pass # down arrow

  # return starting index of group that cursor is in
  def group(self, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return cursor - cursor % self.PageWidth

  # sees whether index is in cursor's group
  def inGroup(self, index, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return index // self.PageWidth == cursor // self.PageWidth
 
  def display(self):
    numArms = len(self.armIDs)

    def printHSep():
      print('   |', end='')
      if self.inSingleMode():
        for i in range(numArms):
          if i == self.ixCursor: print('===|', end='')
          else: print('---|', end='')
      else:
        for i in range(numArms):
          if self.inGroup(i):
            if self.inGroup(i+1, i): print('====', end='')
            else: print('===|', end='')
          else: print('---|', end='')
      print('')

    printHSep()

    print('x: |', end='')
    for i in range(numArms):
      print('{0:^3}|'.format(self.getAngle('x', i)), end='')
    print('')

    printHSep() 
     
    print('y: |', end='')
    for i in range(numArms):
      print('{0:^3}|'.format(self.getAngle('y', i)), end='')
    print('')

    printHSep()

    print('i: |', end='')
    for i in range(numArms):
      print('{0:^3}|'.format(ucLEDs.get(i//self.PageWidth)), end='')
    print('')

    printHSep()


class SliderView:
  def __init__(self): 
    self.lineInputKey = 'c'
    self.ixCursor = 0
    self.NumChannels = DMX.NumChannels
    self.MinValue = 0
    self.MaxValue = 255

    self.PageWidth = 16
 
  def display(self):
      clearScreen()
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      # channel values
      for i in range(ixPageStart, ixPageStart + self.PageWidth):
        print('{0:^4}'.format(DMX.get(i)), end='')
      print('')

      # separator and cursor
      for i in range(ixCursorInPage): print('----', end='')
      print('===-', end='')
      for i in range(self.PageWidth - ixCursorInPage - 1): print('----', end='')
      print('')
      
      # channel numbers
      for i in range(ixPageStart + 1, ixPageStart + self.PageWidth + 1):
        print('{0:^4}'.format(i), end='')
      print('')

  def handleLineInput(self, line):
    tokens = line.split()
    if len(tokens) == 0: return
    cmd = tokens[0]

    try:
      # set a channel or a range of channels (inclusive) to a value
      # channels are 1-based index, so must subtract 1 before indexing
      # usage: (can take multiple arguments)
      # set<value> <channel>
      # set<value> <channel-channel>
      if cmd.startswith('set'):
        value = int(cmd[3:])
        print(value)
        if value < self.MinValue or value > self.MaxValue:
          print('Value', value, ' out of range [0, 255]')
          return

        if len(tokens) == 1:
          v = [value] * self.NumChannels 
          DMX.setAndSend(0, v)
          return

        # handle space-delimited arguments: index or inclusive range (index-index)
        for token in tokens[1:]:
          indices = token.split('-')

          # a single channel index
          if len(indices) == 1:
            DMX.setAndSend(int(indices[0]) - 1, value)
          # argument is a range of channel indices, inclusive, ex: 56-102
          elif len(indices) == 2:
            lower = int(indices[0]) - 1
            upper = int(indices[1])     # inclusive range, so -1 to correct to 0-based index but +1 to include it
            DMX.setAndSend(lower, [value] * (upper - lower))
          else:
            raise BaseException('too many arguments')

      else: print('Unrecognized command')

    except BaseException as e:
      print(e)

  # keyboard input
  def handleChar(self, ch):
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      ch = ch.lower()

      if ch == 'c':
        print('\nEnter command: ', end='')
        line = input().strip()
        if len(line): self.handleLineInput(line)

      elif ch == '0':
        DMX.setAndSend(self.ixCursor, self.MinValue)
      elif ch == '9':
        DMX.setAndSend(self.ixCursor, self.MaxValue)
      
      elif ch == '\x1b':
        seq = getch() + getch()
        if seq == '[A': # up arrow
          DMX.setAndSend(self.ixCursor, min(self.MaxValue, DMX.get(self.ixCursor) + 1))
        elif seq == '[B': # down arrow
          DMX.setAndSend(self.ixCursor, max(self.MinValue, DMX.get(self.ixCursor) - 1))
        elif seq == '[C': # left arrow
          self.ixCursor = min(self.NumChannels-1, self.ixCursor + 1)
        elif seq == '[D': # right arrow
          self.ixCursor = max(0, self.ixCursor - 1)
        elif seq == '[5': # page up
          getch() # eat trailing ~
          self.ixCursor = min(self.NumChannels-1, ixPageStart + self.PageWidth)
        elif seq == '[6': # page down
          getch() # eat trailing ~
          self.ixCursor = max(0, ixPageStart - self.PageWidth)
   
dmxView = SliderView()
lightArmView = LightArmView() 
currentView = lightArmView

def programExit():
  DMX.exit()
  ucServos.exit()
  ucLEDs.exit()
  exit()


if __name__ == '__main__':
  while 1:
    clearScreen()
    currentView.display()
    ch = getch()

    if ch == 'z' or ch == 'Z':
      programExit()
    elif ch == '1':
      currentView = dmxView
    elif ch == '2':
      currentView = lightArmView

    # every view can have a separate key to enter a command line of text
    elif ch == currentView.lineInputKey:
      print('\nEnter command: ', end='')
      line = input()
      tokens = line.split()

      if len(tokens) == 0: continue
      cmd = tokens[0]

      # program-wide commands ?
      try:
        if cmd ==   'exit': programExit()
        elif cmd == 'save': cmdSave(tokens, line)
        elif cmd == 'load': cmdCue(line, CueLoad)
        elif cmd == 'fade': cmdCue(line, CueFade)
        else: currentView.handleLineInput()
      except BaseException as e:
        print(e)
        getch()
        programExit()

    else:
      currentView.handleChar(ch)

