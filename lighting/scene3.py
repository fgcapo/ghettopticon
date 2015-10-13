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

while 1:
  line = input('save, load, or exit: ')
  tokens = line.split()  
  if len(tokens) == 0: continue

  if tokens[0] == 'exit':
    OLA.exit()
    break

  if len(tokens) < 2:
    print('no filename')
    continue

  if tokens[0] == 'save':
    filename = line[4:].strip()
    data = str(list(OLA.data)) 
    #print(data)
    try:
      with open(filename, 'w') as f:
        f.write(data)
    except:
      print('Error saving file')

  elif tokens[0] == 'load':
      filename = line[4:].strip()
    #print(filename)
#    try:
      with open(filename) as f:
        text = f.readline()
        #print(text)
        channels = ast.literal_eval(text)
        print(channels)
        OLA.client.SendDmx(1, channels) 
#    except:
#      print('Error loading file')


  elif tokens[0] == 'fade':
      time = 5.0
      timestep = .1
      filename = line[4:].strip()
    #print(filename)
#    try:
      with open(filename) as f:
        text = f.readline()
        #print(text)
        current = ast.literal_eval(text)
        #print(channels)
        vel = list(channels)
        target = list(OLA.data)
        for i in range(len(channels)):
          vel[i] = (target[i] - current[i]) / time

        for t in range(0, time, timestep):
          current[i] += vel[i]
          time.sleep(timestep)
       
        OLA.client.SendDmx(1, current) 
#    except:
#      print('Error loading file')

