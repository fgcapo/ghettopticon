from trackspot import *
import os, ast

spots = [
      TrackSpot(None, 161, 'w', 's', 'a', 'd', 'e', 'q'),
      TrackSpot(None, 170, '8', '5', '6', '4', '9', '7'),
      TrackSpot(None, 193, 'g', 'b', 'v', 'n', 'h', 'f')]

for filename in os.listdir('scenes'):
  if not os.path.isfile(filename): continue

  with open('scenes/' + filename, 'r') as f:
#    try:
      text = f.read()
      print(text)
      continue


      json = ast.literal_eval(f.read())
      dmx = None
      if isinstance(json, list): dmx = json
      elif isinstance(json, dict): dmx = json['DMX']
      else: raise BaseException('parse error')

      print(dmx)
      for spot in spots:
        if dmx[spot.intensity] == 0 and (dmx[spot.strobe] > 0 or dmx[spot.speed] > 0):
          print('file "' + filename + '" has weirdness on spot', spot.firstChannel)

        elif dmx[spot.intensity] > 0 and (dmx[spot.strobe] == 0 or dmx[spot.speed] == 0):
          print('file "' + filename + '" has weirdness on spot', spot.firstChannel)

 #   except BaseException as e:
  #    print('Error reading file: "' + filename + '":', e)

      

