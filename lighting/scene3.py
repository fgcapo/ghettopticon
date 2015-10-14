import sys
import os
import os.path
import threading
import ast
import time
from ola.ClientWrapper import ClientWrapper

class OlaThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.data = [0] * 512

  def run(self):
    def onData(data):
        # TODO check on status before assigning data
        self.data = data
        #print(data)

    self.wrapper = ClientWrapper()
    self.client = self.wrapper.Client()
    universe = 1
    self.client.RegisterUniverse(universe, self.client.REGISTER, onData)
    print('running OLA thread...')
    self.wrapper.Run()
    # TODO catch exceptions

  def exit(self):
    self.wrapper.Stop()

  def getData(self):
    return self.data

OLA = OlaThread()
OLA.start()

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
  def addCue(self, cue):
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
      with open(filename) as f:
        text = f.readline()
        #print(text)
        self.target = ast.literal_eval(text)
    except OSError as e:
      raise BaseException('Error loading file: ' + str(e))

  def run(self, immediate=False):
    try:
      OLA.client.SendDmx(1, self.target)
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
      with open(filename) as f:
        text = f.readline()
        #print(text)
        self.target = ast.literal_eval(text)
    except (OSError, IOError) as e:
      raise BaseException('Error loading file: ' + str(e))
 
  def run(self, immediate=False):
    try:
      timestep = .05
      current = list(OLA.data)
      vel = [0] * len(current)

      if immediate:
        OLA.client.SendDmx(1, self.target)
        return

      # calculate delta for each timestep
      # -1 means don't change
      for i in range(len(self.target)):
        if self.target[i] >= 0:
          vel[i] = (self.target[i] - current[i]) * (timestep / self.period)

      print('fading for', self.period, 'seconds............................. ', end='', flush=True)

      for t in frange(0, self.period, timestep):
        for i in range(len(current)): current[i] += vel[i]
        channels = [int(x) for x in current] 
        OLA.client.SendDmx(1, channels)
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
  data = str(list(OLA.getData())) 
  #print(data)
  try:
    with open(filename, 'w') as f:
      f.write(data)
  except:
    raise BaseException('Error saving file')



if __name__ == '__main__':
  while 1:
    line = input('> save, load, fade, or exit: ')
    tokens = line.split()  
    if len(tokens) == 0: continue
    cmd = tokens[0]

    if cmd == 'exit':
      OLA.exit()
      break

    try:
      if cmd == 'save':   cmdSave(tokens, line)
      elif cmd == 'load': cmdCue(line, CueLoad)
      elif cmd == 'fade': cmdCue(line, CueFade)
      else: print('Unrecigbuzed command')
    except BaseException as e:
      print(e)

