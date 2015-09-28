#include <SerialCommand.h>

SerialCommand CmdMgr;
const char Channels[] = {9, 10, 11, 12};
const int NumChannels = sizeof(Channels)/sizeof(*Channels);

const char *SetLEDUsageMsg = "Error: takes 4 arguments between 0 and 255";

void cmdUnrecognized(const char *cmd) {
  Serial.println("unrecognized command");
}

// takes 
void cmdSetLEDs() {
  int channelValues[NumChannels];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumChannels) {
      //Serial.println(ErrorUsageMsg);
      return;
    }
  
    char *end;
    channelValues[count++] = strtol(arg, &end, 10);
    if (*end != '\0') {
      //Serial.println(ErrorUsageMsg);
      return;
    }
  }
  
  if(count != NumChannels) {
    //Serial.println(ErrorUsageMsg);
    return;
  }
  
  for(int i = 0; i < NumChannels; i++) {
    analogWrite(Channels[i], channelValues[i]);
  }
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
