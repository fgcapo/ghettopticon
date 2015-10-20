import sys, os, os.path, threading, ast, time
from getch import getch
from ola.ClientWrapper import ClientWrapper

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
      with openCueFile(filename) as f:
        text = f.readline()
        #print(text)
        self.target = ast.literal_eval(text)
    except OSError as e:
      raise BaseException('Error loading file: ' + str(e))

  def run(self, immediate=False):
    try:
      current = DMX.get()

      # allow for value of -1 to not change current value
      for i in range(len(current)):
        if self.target[i] >= 0: current[i] = self.target[i]

      import pdb; pdb.set_trace()
      DMX.setAndSend(0, current)
    except:
      raise BaseException('Error talking to OLA DMX server')

    
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
  #print(data)
  try:
    with openCueFile(filename, 'w') as f: f.write(dmx)
  except:
    raise BaseException('Error saving file')

############################################################################3
# DMX slider data

def clearScreen():
    #os.system('clear')
    print("\x1b[2J\x1b[H", end='')

class SliderView:
  def __init__(self): 
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

    if cmd == 'exit':
      DMX.exit()
      exit() 

    try:
      if cmd == 'save':   cmdSave(tokens, line)
      elif cmd == 'load': cmdCue(line, CueLoad)
      elif cmd == 'fade': cmdCue(line, CueFade)

      # set a channel or a range of channels (inclusive) to a value
      # channels are 1-based index, so must subtract 1 before indexing
      # usage: (can take multiple arguments)
      # set<value> <channel>
      # set<value> <channel-channel>
      elif cmd.startswith('set'):
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
lightArmView = 
currentView = dmxView

def programExit():
  DMX.exit()
  exit()


if __name__ == '__main__':
  while 1:
    currentView.display()
    ch = getch()

    if char == 'z':
      programExit()
    elif ch == '1':
      currentView = dmxView
    elif ch == '2':
      currentView = lightArmView
    else:
      currentView.handleChar(ch)

