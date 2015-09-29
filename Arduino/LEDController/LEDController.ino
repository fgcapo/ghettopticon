// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - leds <int1> <int2> <int3> <int4>, where <intN> is 0-255

#include <SerialCommand.h>

SerialCommand CmdMgr;
const char Channels[] = {2, 3, 4, 5};
const int NumChannels = sizeof(Channels)/sizeof(*Channels);

const char *SetLEDUsageMsg = "Error: takes 4 arguments between 0 and 255";

void cmdUnrecognized(const char *cmd) {
  Serial.println("unrecognized command");
}

// expects 4 space-delimited ints 0-255
void cmdSetLEDs() {
  int channelValues[NumChannels];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumChannels) {
      //Serial.println(SetLEDUsageMsg);
      return;
    }
  
    char *end;
    channelValues[count++] = strtol(arg, &end, 10);
    if (*end != '\0') {
      //Serial.println(SetLEDUsageMsg);
      return;
    }
  }
  
  if(count != NumChannels) {
    //Serial.println(SetLEDUsageMsg);
    return;
  }
  
  for(int i = 0; i < NumChannels; i++) {
    analogWrite(Channels[i], channelValues[i]);
  }
  
  //Serial.println("OK");
}


void setup() {
  CmdMgr.setDefaultHandler(   cmdUnrecognized);
  CmdMgr.addCommand("leds",   cmdSetLEDs);
  
  Serial.begin(9600);
  Serial.println("LED controller");
}

void loop() {
  CmdMgr.readSerial();
}
