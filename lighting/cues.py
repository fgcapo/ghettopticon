import time
from getch import getch
import scene3 as scene
from scene3 import OLA, restAfterWord, Cue

CuesFilename = 'cuesheet3.txt'

def openCueFile(filenameOnly, mode):
  return open('scenes/' + filenameOnly, mode)


class Scene:
  def __init__(self, name):
    self.name = name
    self.cues = []
  def add(self, cue):
    self.cues.append(cue)


class CueEngine:
  def __init__(self):
    self.scenes = [Scene('Beginning Blackout')]
    self.scenes[0].add(scene.CueLoad('load off'))
    self.ixScene = 0  # current scene
    self.ixCue = -1   # cue we just ran
  
  def thisScene(self): return self.scenes[self.ixScene]
  def thisCue(self):   return self.thisScene().cues[self.ixCue]

  def add(self, scene):
    self.scenes.append(scene)

  def getLoc(self):
    return (self.ixScene, self.ixCue)

  def onLastCue(self):
    return 1+self.ixCue >= len(self.thisScene().cues)
  def onLastScene(self):
    return 1+self.ixScene >= len(self.scenes)
  def onFirstScene(self):
    return self.ixScene <= 0

  def nextCue(self):
    if self.onLastCue():
      if self.onLastScene():
        print(self.getLoc(), 'At End')
        return
      self.ixScene += 1
      self.ixCue = 0
      print('--------------------------------------------------------------')
      print(self.getLoc(), 'Scene:', self.thisScene().name)
    else:
      self.ixCue += 1

    print(self.getLoc(), 'next cue:', self.thisCue().line.strip())
    self.thisCue().run()

  def prevCue(self):
    if self.ixCue <= 0:
      if self.onFirstScene():
        print(self.getLoc(), 'At Beginning')
        return
      self.ixScene -= 1
      self.ixCue = len(self.thisScene().cues) - 1
      print(self.getLoc(), 'Scene:', self.thisScene().name)
    else:
      self.ixCue -= 1

    print(self.getLoc(), 'previous cue:', self.thisCue().line.strip())
    self.thisCue().run(True)

  def nextScene(self): 
    if self.onLastScene():
      print(self.getLoc(), 'On Last Scene')
      return
    self.ixScene += 1
    self.ixCue = -1
    print(self.getLoc(), 'next Scene:', self.thisScene().name)

  def prevScene(self):
    if self.onFirstScene():
      print(self.getLoc(), 'On First Scene')
      return
    self.ixScene -= 1
    self.ixCue = -1
    print(self.getLoc(), 'previous Scene:', self.thisScene().name)


CueMgr = CueEngine()

# parse the cues file
with open(CuesFilename) as f:
  lineNum = 0
  curScene = None
  indentStack = []  # stack of tuples of (node, indent_len)

  def pushIndent(node, indentLen): indentStack.append((node, indentLen))
  def popIndent(): indentStack.pop()
  def topIndent(): return indentStack[-1]
  def topIndentLen(): return indentStack[-1][1]

  seenTab, seenSpace = False, False
  pushIndent(CueMgr, -1)

  line = f.readline()
  while line:
    lineNum += 1
    tokens = line.split()
    
    # skip empty lines and lines where the first token is #
    if len(tokens) and not tokens[0].startswith('#'): 
      cmd = tokens[0]
      indent = line[:line.find(cmd)]
      indentLen = len(indent)
      thisNode = None

      #test for mixed indentation characters
      if indent.find(' ') >= 0: seenSpace = True
      if indent.find('\t') >= 0: seenTab = True
      if seenSpace and seenTab:
        print('The cue file mixes spaces and tabs.  Please use one or the other')
        exit()
      
      # remove cmds with <= indent, because their block/revelance is over
      # TODO handle this indentation error case:
      # s
      #   s
      #  s
      while indentLen <= topIndentLen():
        popIndent()

      try:
        if cmd == 'scene':
          thisNode = Scene(restAfterWord(cmd, line))
        elif cmd == 'seq':
          thisNode = scene.CueSequence(line)
        elif cmd == 'load':
          thisNode = scene.CueLoad(line)
        elif cmd == 'fade':
          thisNode = scene.CueFade(line)
        else:
          print('Error unrecognized command on line', lineNum)
          print('Text:', line)

      except BaseException as e:
        print(e)
        print('Line Number:', lineNum)
        print('Text:', line)

      if thisNode:
        topIndent()[0].add(thisNode)
        pushIndent(thisNode, indentLen)
 
    line = f.readline()

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
    v = OLA.lastDataSent[channel]
    v = min(255, max(0, v+inc))
    print(channel, '=', OLA.lastDataSent[channel], '->', v)
    OLA.lastDataSent[channel] = v
    OLA.send(OLA.lastDataSent)


if __name__ == '__main__':
  # wait for OLA client to connect
  time.sleep(1)
  print('z:     exit')
  print('Space: next cue')
  print('/:     previous cue')
  print('>:     next scene')
  print('<:     previous scene')
  print('----------------------')
  print('Press Space initially to black out lights:')
#  scene.CueLoad('load blackout').run()

  spotLeft =  TrackSpot(162, 161, 166, 'w', 's', 'a', 'd', 'e', 'q')
  spotRight = TrackSpot(171, 170, 175, '8', '5', '6', '4', '9', '7')
  spotCenter = TrackSpot(194, 193, 198, 'g', 'b', 'v', 'n', 'h', 'f')

  while 1:
    ch = getch().lower()
    if ch == 'z':
      OLA.exit()
      break
    elif ch == ' ':
      CueMgr.nextCue()
    elif ch == '/':
      CueMgr.prevCue()
    elif ch == '.' or ch == '>':
      CueMgr.nextScene()
    elif ch == ',' or ch == '<':
      CueMgr.prevScene()
    elif ch == 'p':
      print(OLA.lastDataSent)

    # track spots off or on
    elif ch == 't':
     OLA.lastDataSent[197] = OLA.lastDataSent[165] = OLA.lastDataSent[174] = 255
     OLA.send(OLA.lastDataSent)
    elif ch == 'y':
     OLA.lastDataSent[197] = OLA.lastDataSent[165] = OLA.lastDataSent[174] = 0
     OLA.send(OLA.lastDataSent)

    # manual control of track spots
    else:
      spotLeft.onKey(ch)
      spotRight.onKey(ch) 
      spotCenter.onKey(ch)


