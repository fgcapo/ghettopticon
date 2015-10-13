import sys
import os
import os.path
import threading
from ola.ClientWrapper import ClientWrapper
import ast
import time

class OlaThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.data = None

    def run(self):
        def onData(data):
            # TODO check on status before assigning data
            self.data = data
            #print(data)

        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        universe = 1
        self.client.RegisterUniverse(universe, self.client.REGISTER, onData)
        print('running OLA thread')
        self.wrapper.Run()
        # TODO catch exceptions

    def exit(self):
        #try: self.wrapper.Terminate()
        self.wrapper.Stop()

    def getData(self):
        # return or print?
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

while 1:
  line = input('> save, load, fade, or exit: ')
  tokens = line.split()  
  if len(tokens) == 0: continue

  if tokens[0] == 'exit':
    OLA.exit()
    break

  # save current OLA scene
  if tokens[0] == 'save':
    if len(tokens) < 2:
      print('no filename')
      continue

    filename = line[4:].strip()
    data = str(list(OLA.data)) 
    #print(data)
    try:
      with open(filename, 'w') as f:
        f.write(data)
    except:
      print('Error saving file')

  # load scene from local file
  elif tokens[0] == 'load':
    if len(tokens) < 2:
      print('no filename')
      continue

    filename = line[4:].strip()
    try:
      with open(filename) as f:
        text = f.readline()
        print(text)
        channels = ast.literal_eval(text)
        OLA.client.SendDmx(1, channels) 
    except:
      print('Error loading file')

  # fade from current scene to new scene
  # usage:
  # fade <optional time in seconds> <filename>
  elif tokens[0] == 'fade':
    timestep = .05
    if len(tokens) < 2:
      print('usage: fade <optional time in seconds> <filename>')
      continue

    try:  
      tok = tokens[1]
      period = float(tok)
      filename = line[line.find(tok) + len(tok):].strip()
    except:
      period = 5.0
      filename = line[4:].strip()

    try:      
      with open(filename) as f:
        text = f.readline()
        print(text)
        target = ast.literal_eval(text)
        current = list(OLA.data)
        vel = [0] * len(target)

        print('fading for', period, 'seconds...')

        for i in range(len(channels)):
          vel[i] = (target[i] - current[i]) * (timestep / period)

        for t in frange(0, period, timestep):
          for i in range(len(current)): current[i] += vel[i]
          channels = [int(x) for x in current] 
          OLA.client.SendDmx(1, channels) 
          time.sleep(timestep)
    except (OSError, IOError) as e:
      print('Error loading ')
    # TODO other exceptions having to do with the fade math

  else:
    print('Unknown command')
