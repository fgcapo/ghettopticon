// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - pwm <int1> <int2> <int3> ..., where <intN> is 0-255 and N is up to NumChannels
//////////////////////////////////////////////////////////////////////////////////////

#include <SC.h>

// Comment this out to read and write from Serial instead of Ethernet.
// Arduino IDE is wigging out when selecting which ethernet library to use; see line 35.
//#define COMM_ETHERNET

// this flag will invert PWM output (255-output), for active-low devices
#define INVERT_HIGH_AND_LOW


// Ethernet via ENC28J60 
// Library: https://github.com/ntruchsess/arduino_uip
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Pinout - Arduino Mega:
// VCC (Green) -   3.3V
// GND (Gr Wh) -    GND 
// SCK (Bl Wh) - Pin 52
// SO  (Blue)  - Pin 50
// SI  (Br Wh) - Pin 51
// CS  (Brown) - Pin 53  # Selectable with the ether.begin() function
//
// Pinout - Arduino Uno:
// VCC (Green) -   3.3V
// GND (Gr Wh) -    GND
// SCK (Bl Wh) - Pin 13
// SO  (Blue)  - Pin 12
// SI  (Br Wh) - Pin 11
// CS  (Brown) - Pin 8   # Selectable with the ether.begin() function
#ifdef COMM_ETHERNET
  
  // For ENC28J60 card
  #include <UIPEthernet.h>
  
  // For Arduino Ethernet Shield
  //#include <SPI.h>
  //#include <Ethernet.h>

  const char ID_IP = 71;

  IPAddress IP(10,0,0,ID_IP);
  IPAddress GATEWAY(10,0,0,1);
  IPAddress SUBNET(255, 255, 255, 0);
  const unsigned int PORT = 1337;
  static uint8_t MAC[6] = {0x00,0x01,0x02,0x03,0xa4,ID_IP};

  EthernetServer TCPserver(PORT);

  // print to the current ethernet client if there is one
  EthernetClient Client;
  #define gPrinter Client
#endif

  //#define gPrinter Serial
#include <PrintLevel.h>

void cmdUnrecognized(const char *cmd);
void cmdPWMPins();
void cmdSetPrintLevel();

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"pwm",    cmdPWMPins},
  {NULL,     NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);
const int Channels[] = {3, 5, 6, 9, 10, 11};  // Arduino Uno PWM pins
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
    
    printInfo("Setting pin ");
    printInfo(Channels[count]);
    printInfo(" to ");
    printlnInfo(v);
    channelValues[count++] = v;
  }
  
  if(count == 0) {
    printlnError("Error: no arguments");
    return;
  }
  
  for(int i = 0; i < count; i++) {
    int c = channelValues[i];
#ifdef INVERT_HIGH_AND_LOW
    c = 255 - c;
#endif
    analogWrite(Channels[i], c);
  }
  
  printAck("OK set ");
  printAck(count);
  printlnAck(" pins");
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
  
  printAck("print level ");
  printlnAck(PrintLevel::toString());
}

void setup() {
  Serial.begin(38400);
  printAlways("PWM controller. PWM pins are expected to be ");
  
  for(int i = 0; i < NumChannels; i++) {
    pinMode(Channels[i], OUTPUT);
    
    // high = off, so start high
    analogWrite(Channels[i], 255);

    if(i != 0) printAlways(", ");
    printAlways(Channels[i]);
  }
  
  printAlways(".\n");

#ifdef COMM_ETHERNET
  // setup ethernet module
  // TODO: assign static IP based on lowest present servo ID
  Serial.print("Starting ethernet server on address: ");

  Ethernet.begin(MAC, IP);//, GATEWAY, SUBNET);
    
  TCPserver.begin();
  Serial.println(Ethernet.localIP());
#endif

  // fiddle with PWM frequency
  //TCCR2B = _BV(CS00);
  /*TCCR0B = TCCR0B & 0b11111000 | 1;
  TCCR1B = TCCR1B & 0b11111000 | 1;
  TCCR2B = TCCR2B & 0b11111000 | 1;*/
}

void loop() {
// read from EITHER serial OR network; otherwise we'll need multiple read buffers...
#ifndef COMM_ETHERNET
  CmdMgr.readSerial();

#else
  // TODO: edit EthernetServer to separate accepting a connection
  // from reading from one, so we can great connectors
  // Multiple connections? Yikes. Requires multiple buffers. Probably not.

  // see if a client wants to say something; if so, save them as the client to respond to
  if(EthernetClient client = TCPserver.available()) {
    //client.println("Allo");
    Client = client;
  }

  if(Client)
  {
    //bool gotData = false;
    while(Client.available() > 0)
    {
      char c = Client.read();
      CmdMgr.handleChar(c);
      //gotData = true;
    }
    //if(gotData) Client.println("DATA from Server!");
  }
#endif
}
