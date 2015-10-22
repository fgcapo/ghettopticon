import sys, os, os.path, threading, ast, time
from console import * 
from cue import *
from cueengine import CueEngine, CuesFilename

CueMgr = CueEngine()

def restAfterWord(word, line):
  return line[line.find(word) + len(word):].strip()

def fitServoRange(v): return max(212, min(812, v))
def fitLEDRange(v): return max(0, min(255, v))

class Increment:
  def __init__(self, possibilities):
    self.modes = possibilities
    if self.modes == None: self.modes = [1, 5, 20]
    self.current = 0    #index into possibilities

  def __call__(self): return self.modes[self.current]
  def prev(self): self.current = max(0, min(len(self.modes)-1, self.current - 1))
  def next(self): self.current = max(0, min(len(self.modes)-1, self.current + 1))
    

class View:
  def __init__(self):
    self.lineInputKey = 'c'
  def onFocus(self): pass
  def display(self): pass
  def handleChar(self): pass


class LightArmView:
  def __init__(self):
    self.lineInputKey = 'c'

    # ID of base servo; will they all be the same dimension?
    # other servo will be ID+1
    self.armIDs = [25, 29, 27, 17]#, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    for id in self.armIDs:
      ucServos.set(id, 512)
      ucServos.set(id+1, 512)

    self.PageWidth = 4    
    self.ixCursor = 0
    
    self.mode = 0   # index into self.Modes
    self.inc = Increment([1, 5, 20])

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
    elif type != 'x': raise BaseException('bad dimension')
    return ucServos.get(id)

  # returns a list of the selected indices
  def selected(self):
    if self.inSingleMode():
      return [self.ixCursor]
    else:
      return range(self.group(), self.PageWidth)

  def selectedIDs(self):
    ids = []
    for i in self.selected():
      ids.append(self.armIDs[i])
      ids.append(self.armIDs[i] + 1)
    return ids
     
  # return starting index of group that cursor is in
  def group(self, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return cursor - cursor % self.PageWidth

  # sees whether index is in cursor's group
  def inGroup(self, index, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return index // self.PageWidth == cursor // self.PageWidth
 
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
    if ch == 'r': 
      ucServos.relax(self.selectedIDs())
    if ch == '0':
      for i in self.selected():
        ucServos.set(self.armIDs[i], 512)
        ucServos.set(1 + self.armIDs[i], 512)
    if ch == '9':
      for i in self.selected():
        ucServos.set(self.armIDs[i], 300)
        ucServos.set(1 + self.armIDs[i], 300)
    if ch == '8':
      for i in self.selected():
        ucServos.set(self.armIDs[i], 700)
        ucServos.set(1 + self.armIDs[i], 700)

    elif ch == 'w':
      self.modY(self.inc())
    elif ch == 's':
      self.modY(-self.inc())
    elif ch == 'a':
      self.modX(self.inc())
    elif ch == 'd':
      self.modX(-self.inc())
    elif ch == 'q':
      self.modI(self.inc())
    elif ch == 'e':
      self.modI(-self.inc())

    elif ch == '<' or ch == ',':
      self.inc.prev()
    elif ch == '>' or ch == '.':
      self.inc.next()


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

  def onFocus(self):
    pass

  def display(self):
    clearScreen()
    numArms = len(self.armIDs)

    def printHSep(firstColBlank=True):
      if firstColBlank: print('   |', end='')
      else: print('---|', end='')

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

    print('   Light Arm View')
    printHSep(False)

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

    printHSep(False)


class SliderView:
  def __init__(self): 
    self.lineInputKey = 'c'
    self.ixCursor = 0
    self.NumChannels = DMX.NumChannels
    self.MinValue = 0
    self.MaxValue = 255

    self.PageWidth = 16
 
  def onFocus(self):
    pass

  def display(self):
      clearScreen()
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      print('                           DMX View')
      for i in range(self.PageWidth): print('----', end='')
      print('')

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

      if ch == '0':
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



class TrackSpot:
  def __init__(self, x, y, lum, up, down, left, right, brighter, darker):
    self.x = x-1
    self.y = y-1
    self.lum = lum-1
    self.up = up
    self.down = down
    self.left = left
    self.right = right
    self.brighter = brighter
    self.darker = darker

  def onKey(self, ch):
    inc = 5
    if ch == self.up:         self.set(self.x, inc)
    elif ch == self.down:     self.set(self.x, -inc)
    elif ch == self.left:     self.set(self.y, inc)
    elif ch == self.right:    self.set(self.y, -inc)
    elif ch == self.brighter: self.set(self.lum, inc)
    elif ch == self.darker:   self.set(self.lum, -inc)
    else: return

  def set(self, channel, inc):
    v = DMX.get(channel)
    u = min(255, max(0, v + inc))
    print(channel, '=', v, '->', u)
    DMX.setAndSend(channel, u)


class CueView:
  def __init__(self):
    self.lineInputKey = 'c'
    self.spotLeft =  TrackSpot(162, 161, 166, 'w', 's', 'a', 'd', 'e', 'q')
    self.spotRight = TrackSpot(171, 170, 175, '8', '5', '6', '4', '9', '7')
    self.spotCenter = TrackSpot(194, 193, 198, 'g', 'b', 'v', 'n', 'h', 'f')

    CueMgr.loadCueSheet(CuesFilename)

  def onFocus(self):
    clearScreen()
    print('z:     exit')
    print('Space: next cue')
    print('/:     previous cue')
    print('>:     next scene')
    print('<:     previous scene')
    print('----------------------')
    if CueMgr.ixCue < 0:
      print('Next Cue: ', end=''); CueMgr.printLocStr()
    else:
      print('Currently At Cue: ', end=''); CueMgr.printLocStr()
    print('----------------------')
    #print('Press Space initially to black out lights:')

  def display(self): pass

  def handleChar(self, ch):
    if ch == ' ':
      CueMgr.nextCue()
    elif ch == '/':
      CueMgr.prevCue()
    elif ch == '.' or ch == '>':
      CueMgr.nextScene()
    elif ch == ',' or ch == '<':
      CueMgr.prevScene()

    # track spots off or on
    elif ch == 't':
      for c in [197, 165, 174]: DMX.set(c, 255)
      DMX.send()
    elif ch == 'y':
      for c in [197, 165, 174]: DMX.set(c, 0)
      DMX.send()

    # manual control of track spots
    else:
      self.spotLeft.onKey(ch)
      self.spotRight.onKey(ch) 
      self.spotCenter.onKey(ch)

  def handleLineInput(self, line):
      tokens = line.split()
      cmd = tokens[0]

      if cmd == 'cuesheet':
        CueMgr.loadCueSheet(restAfterWord(cmd, line))
        self.onFocus()


dmxView = SliderView()
lightArmView = LightArmView() 
cueView = CueView()

currentView = dmxView

def programExit():
  DMX.exit()
  ucServos.exit()
  ucLEDs.exit()
  exit()


if __name__ == '__main__':
  clearScreen()
  currentView.onFocus()

  # wait for OLA client to connect?

  while 1:
    currentView.display()
    ch = getch()

    if ch == 'z' or ch == 'Z':
      programExit()

    elif ch == '1': 
      currentView = cueView
      currentView.onFocus()
    elif ch == '2': 
      currentView = dmxView
      currentView.onFocus()
    elif ch == '3':
      currentView = lightArmView
      currentView.onFocus()

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
        #elif cmd == 'cuesheet': loadCueSheet(line) # handled in cview
        else: currentView.handleLineInput(line)
      except ArithmeticError as e:
        print(e)
        getch()
        programExit()

    else:
      currentView.handleChar(ch)

