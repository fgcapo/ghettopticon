// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - leds <int1> <int2> <int3> <int4> <int5> <int6>, where <intN> is 0-255
#include <SerialCommand.h>
#include <PrintLevel.h>


SerialCommand CmdMgr;
const char Channels[] = {3, 5, 6, 9, 10, 11};  // Arduino Uno PWM pinss
const int NumChannels = sizeof(Channels)/sizeof(*Channels);

const char *SetLEDUsageMsg = "Error: takes 6 arguments between 0 and 255";


void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

// expects 4 space-delimited ints 0-255
void cmdSetLEDs() {
  int channelValues[NumChannels];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumChannels) {
      printlnError(SetLEDUsageMsg);
      return;
    }
  
    char *end;
    channelValues[count++] = strtol(arg, &end, 10);
    if (*end != '\0') {
      printlnError(SetLEDUsageMsg);
      return;
    }
  }
  
  if(count != NumChannels) {
    printlnError(SetLEDUsageMsg);
    return;
  }
  
  for(int i = 0; i < NumChannels; i++) {
    analogWrite(Channels[i], channelValues[i]);
  }
  
  printlnAck("OK");
}

void cmdSetPrintLevel() {  
  if(char *arg = CmdMgr.next()) {
    if(CmdMgr.next()) {
      printlnAlways("Error: takes 0 or 1 arguments");
      return;
    }
    
    if(!PrintLevel::set(arg)) {
      PrintLevel::printErrorString();
      return;
    }
  }
  
  printAlways("print level ");
  printlnAlways(PrintLevel::toString());
}

void setup() {
  CmdMgr.setDefaultHandler(   cmdUnrecognized);
  CmdMgr.addCommand("plevel", cmdSetPrintLevel);
  CmdMgr.addCommand("leds",   cmdSetLEDs);
  
  Serial.begin(38400);
  printlnAlways("LED controller");

  for(int i = 0; i < NumChannels; i++) {
    pinMode(Channels[i], OUTPUT);
  }

  // fiddle with PWM frequency
  //TCCR2B = _BV(CS00);
  /*TCCR0B = TCCR0B & 0b11111000 | 1;
  TCCR1B = TCCR1B & 0b11111000 | 1;
  TCCR2B = TCCR2B & 0b11111000 | 1;*/
}

void loop() {
  CmdMgr.readSerial();
}
