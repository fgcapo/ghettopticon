// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - pwm <int1> <int2> <int3> ..., where <intN> is 0-255 and N is up to NumChannels

#include <SC.h>
#include <PrintLevel.h>

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"pwm",    cmdPWMPins},
  {NULL,     NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);
const char Channels[] = {3, 5, 6, 9, 10, 11};  // Arduino Uno PWM pins
const int NumChannels = sizeof(Channels)/sizeof(*Channels);

const char *SetPWMUsageMsg = "Error: takes up to 6 arguments between 0 and 255";


void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

// expects up to 6 space-delimited ints 0-255
void cmdPWMPins() {
  int channelValues[NumChannels];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumChannels) {
      printlnError(SetPWMUsageMsg);
      return;
    }
  
    char *end;
    long v = strtol(arg, &end, 10);
    if (*end != '\0' || v < 0 || v > 255) {
      printlnError(SetPWMUsageMsg);
      return;
    }
    
    channelValues[count++] = v;
  }
  
  if(count == 0) {
    printlnError("Error: no arguments");
    return;
  }
  
  for(int i = 0; i < count; i++) {
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
  Serial.begin(38400);
  printAlways("PWM controller. PWM pins are expected to be ");
  
  for(int i = 0; i < NumChannels; i++) {
    pinMode(Channels[i], OUTPUT);

    if(i != 0) printAlways(", ");
    printAlways((int)Channels[i]);
  }
  
  printAlways(".\n");

  // fiddle with PWM frequency
  //TCCR2B = _BV(CS00);
  /*TCCR0B = TCCR0B & 0b11111000 | 1;
  TCCR1B = TCCR1B & 0b11111000 | 1;
  TCCR2B = TCCR2B & 0b11111000 | 1;*/
}

void loop() {
  CmdMgr.readSerial();
}
