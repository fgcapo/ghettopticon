import time
from getch import getch
import scene3 as scene
from scene3 import OLA, restAfterWord, Cue

CuesFilename = 'cuesheet.txt'

class Scene:
  def __init__(self, name):
    self.name = name
    self.cues = []
  def addCue(self, cue):
    self.cues.append(cue)

class CueEngine:
  def __init__(self):
    self.scenes = [Scene('Beginning')]
    self.scenes[0].addCue(scene.CueLoad('load off'))
    self.ixScene = 0  # current scene
    self.ixCue = -1   # cue we just ran
  
  def thisScene(self): return self.scenes[self.ixScene]
  def thisCue(self):   return self.thisScene().cues[self.ixCue]

  def addScene(self, scene):
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


with open(CuesFilename) as f:
  curScene = None
  #groupStack = []
  #def pushGroup(cmd, indent): groupStack.append((cmd, indent))
  #def lastGroupIndent(): return groupStack[-1][1]
  numSeqLeft = 0
  curSeq = None

  line = f.readline()
  while line:
    tokens = line.split()
    if len(tokens): 
        cmd = tokens[0]
      #indent = line[:line.find(cmd)]
      #while(len(indent) < len(lastGroupIndent)

      #try:
        if cmd == 'scene':
          curScene = Scene(restAfterWord(cmd, line))
          CueMgr.addScene(curScene)
        elif cmd == 'seq':
          curSeq = scene.CueSequence(line)
          try:
            token = tokens[1]
            numSeqLeft = int(token)
          except:
            print('Error: seq needs to be followed by the number of cues')
            #OLA.exit()
            exit()
          curScene.addCue(curSeq)

        elif cmd == 'load':
          cue = scene.CueLoad(line)
          if not curSeq: curScene.addCue(cue)
          else:
            curSeq.addCue(cue)
            numSeqLeft -= 1
            if numSeqLeft == 0: curSeq = None
          
        elif cmd == 'fade':
          cue = scene.CueFade(line)
          if not curSeq: curScene.addCue(cue)
          else:
            curSeq.addCue(cue)
            numSeqLeft -= 1
            if numSeqLeft == 0: curSeq = None

        else:
          print('Error unrecognized command')
          print('Text', line)

      #except BaseException as e:
      #  print(e)
      #  print('Text', line)

    line = f.readline()

if __name__ == '__main__':
  # wait for OLA client to connect
  time.sleep(1)
  print('z:     exit')
  print('Space: next cue')
  print('b:     previous cue')
  print('>:     next scene')
  print('<:     previous scene')
  print('----------------------')
  print('Press Space initially to black out lights:')
#  scene.CueLoad('load blackout').run()

  while 1:
    ch = getch().lower()
    if ch == 'z':
      OLA.exit()
      break
    elif ch == ' ':
      CueMgr.nextCue()
    elif ch == 'b' or ch == 'B':
      CueMgr.prevCue()
    elif ch == '.' or ch == '>':
      CueMgr.nextScene()
    elif ch == ',' or ch == '<':
      CueMgr.prevScene()


