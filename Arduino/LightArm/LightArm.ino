#include <ax12.h>
#include <BioloidController2.h>    // use the bug-fixed version 
#include <PrintLevel.h>
#include <SC.h>

/////////////////////////////////////////////////////////////////////////////////
// globals

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"speed",  cmdSetMaxSpeed},
  {"v",      readVoltage},
  {"r",      readServoPositions},
  {"s",      cmdSetServoPosition},
  {"B",      cmdSetServoPositionBinary},
  {"relax",  cmdRelax},
  {"torq",   cmdTorque},
  {NULL,     NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);

const int NumServos = 32;
BioloidController Servos(1000000);

// When a move is requested, the servos will move at different speeds in order to arrive
// at the target position simultaneously. But movement time will be constrained so that
// no servo will move faster than this maximum speed, constrained to [1-1000].
// Speed is inverted to simplify calculation.
int gMaxSpeedInv = 10;  // max servo movement speed inverted, in ms per angle-unit

bool relaxed = false;

/////////////////////////////////////////////////////////////////////////////////////////////
// helpers

// Converts string to double; returns true if successful.
// Returns false if str contains any inappropriate characters, including whitespace.
// See strtod for accepted number formats.
boolean toDouble(const char *str, double *result) {
  char *end;
  if(*str == ' ') return false;
  *result = strtod(str, &end);

  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// Converts string to long; returns true if successful.
// Returns false if str contains any characters other than numbers or a negative sign.
boolean toLong(const char *str, long *result) {
  char *end;
  //if(*str == ' ') return false;
  *result = strtol(str, &end, 10);
  
  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// converts string to int; returns true if successful
// Returns false if str contains any characters other than numbers or a negative sign.
boolean toInt(const char *str, int *result) {
  char *end;
  //if(*str == ' ') return false;
  long r = strtol(str, &end, 10);
  
  // TODO check if out of int range
  //if((unsigned long)r >> (8*sizeof(*result))) return false;
  *result = r;
  
  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

//////////////////////////////////////////////////////////////////////////////////
// commands
void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

void readVoltage() {
  float voltage = (ax12GetRegister (1, AX_PRESENT_VOLTAGE, 1)) / 10.0; 
  if(voltage < 0) {
    printlnError("Dynamixel error: system reported voltage error. May be servos with duplicate IDs.");
  }
  else {
    printError("Dynamixel ready. System voltage: ");
    printError(voltage);
    printlnError("V");
  }
}


void cmdRelax() {
  
  const int maxAngles = NumServos;
  int ids[maxAngles];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumServos) {
      printlnError("Error: too many IDs");
      return;
    }
    
    int id;

    if(!toInt(arg, &id) || id < 1 || id > 127) {
      printlnError("Error: ID must be between 1 and 127");
      return;
    }
    
    ids[count++] = id;
  }
  
  if(count == 0) {
    count = NumServos;
    for(int i = 0; i < NumServos; i++) {
      Relax(Servos.getId(i));
    }
  }
  else {
    for(int i = 0; i < count; i++) {
      Relax(ids[i]);
    }
  }
  
  // TODO not sure how useful a single flag is
  //relaxed = true;
  
  printAck("Relaxed ");
  printAck(count);
  printlnAck(" Servos");
}

void cmdTorque() {
  
  const int maxAngles = NumServos;
  int ids[maxAngles];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    int id;

    if(!toInt(arg, &id) || id < 1 || id > 127) {
      printlnError("Error: ID must be between 1 and 127");
      return;
    }
    
    ids[count++] = id;
  }
  
  if(count == 0) {
    count = NumServos;
    for(int i = 0; i < NumServos; i++) {
      TorqueOn(Servos.getId(i));
    }
  }
  else {
    for(int i = 0; i < count; i++) {
      TorqueOn(ids[i]);
    }
  }
  
  // TODO not sure how useful a single flag is
  //relaxed = true;
  
  printAck("Enabled torque on ");
  printAck(count);
  printlnAck(" Servos");
}


// if no argument, prints the maximum speed
// if one argument, sets the maximum speed and then prints it
// Units to the user are angle-units per second, valid range [1-1000]
// Internally the speed is kept in ms per angle-unit, valid range [1000-1]
void cmdSetMaxSpeed() {
  if(char *arg = CmdMgr.next()) {
    if(CmdMgr.next()) {
      printlnError("Error: takes 0 or 1 arguments");
      return;
    }

    double speed;
    if(!toDouble(arg, &speed) || speed < 1 || speed > 1000) {
      printlnError("Error: speed is in angle-units per second; between 1 and 1000");
      return;
    }
    
    gMaxSpeedInv = (int)(1000.0 / speed);  // convert to ms per angle-unit
  }
  
  printAck("max speed in angle-units per second: ");
  printlnAck(1000.0 / gMaxSpeedInv);  // convert to angle-units per second
}

void readServoPositions() {
  printAck("Servo Readings:");
  printlnAck(NumServos);
  
  Servos.readPose();

  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    int pos = Servos.getCurPose(id);
    //int pos = Servos.readPose(i); //in case we've relaxed and some one manually moved the servos
    //Serial.print(pos);
    
    if(pos > 2000) pos = 0;   // 8191-2 is invalid; replace with 0 because it's also invalid and shorter
    
    // print key:value pairs space delimited, but column-aligned
    char buf[16];
    int ixEnd = sprintf(buf, "ID:%d", id);
    while(ixEnd < 5) buf[ixEnd++] = ' ';
    buf[ixEnd] = '\0';

    printAck(buf);
    printAck(" pos:");
    printlnAck(pos);
  }

  // python dictionary notation  
  char dictBuf[256] = "{";
  int ix = 1;

  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    int pos = Servos.getCurPose(id);

    if(i != 0) dictBuf[ix++] = ',';
    ix += sprintf(dictBuf+ix, "%d:%d", id, pos);
  }
  
  sprintf(dictBuf+ix, "}");
  printlnAlways(dictBuf);
}

//servo serial command format:
//"s <id>:<angle> <id>:<angle> ... \n"
//angle is 0 to 1024? or 1 to 1023?
// We shall constrain the angle to 200 to 824, and assume and consider 0 a no-op.
void cmdSetServoPosition() {
  const char *FormatErrorMsg = "Error: takes pairs in the form <ID>:<angle>";

  struct Tuple { int id, angle; };
  
  const int maxAngles = NumServos;
  Tuple angles[maxAngles];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    int id, angle;

    char *sID = strtok(arg, ":");
    if(sID == NULL) {
      printlnError(FormatErrorMsg);
      return;
    }
    if(!toInt(sID, &id) || id < 1 || id > 127) {
      printlnError("Error: ID must be between 1 and 127");
      return;
    }

    char *sAngle = strtok(NULL, ":");
    if(sAngle == NULL) {
      printlnError(FormatErrorMsg);
      return;
    }
    //contrain from -90 to 90 degrees
    if(!toInt(sAngle, &angle) || angle < 200 || angle > 824) {
      printlnError("Error: angle must be between 200 and 824");
      return;
    }
    
    angles[count].id = id;
    angles[count].angle = angle;
    count++;
  }
  
  if(count == 0) {
    printlnError("Error: no arguments");
    return;
  }
  
  if(relaxed) {
    relaxed = false;
    Servos.readPose();
  }

  long msLargestTimeToMove = 0;
  for(int i = 0; i < count; i++) {
    int id = angles[i].id;
    int newAngle = angles[i].angle;
    int curAngle = Servos.getCurPose(id);
    
    if(curAngle < 1 || curAngle > 2000) continue;
    
    long time = abs(curAngle - newAngle) * gMaxSpeedInv;
    msLargestTimeToMove = max(msLargestTimeToMove, time);
    
    printInfo("moving id ");
    printInfo(id);
    printInfo(" from ");
    printInfo(curAngle);
    printInfo(" to ");
    printlnInfo(newAngle);

    Servos.setNextPose(id, newAngle);
  }
  
  printAck("Longest movement will take ");
  printAck(msLargestTimeToMove);
  printlnAck(" ms");
  
  Servos.interpolateSetup(round(msLargestTimeToMove));
}

void setServoPositionBinary(char *buffer, int len) {
  int numAngles = min(len/2, NumServos);
  long msLargestTimeToMove = 0;
  
  if(relaxed) {
    relaxed = false;
    Servos.readPose();
  }
  
  for(int i = 0; i < numAngles; i++) {
    // little endian
    int newAngle = (unsigned char)buffer[2*i];
    newAngle    += (int)((unsigned)buffer[2*i+1]) << 8;
    
    // 0 is no-op; acceptable range is [200, 824]
    if(newAngle == 0) continue;
    if(newAngle < 200 || newAngle > 824) {
      printError("Angle out of range: ");
      printlnError(newAngle);
      continue;
    }
    
    int id = Servos.getId(i);
    int curAngle = Servos.getCurPose(id);
    if(curAngle < 1 || curAngle > 2000) continue;
    
    long time = abs(curAngle - newAngle) * gMaxSpeedInv;
    msLargestTimeToMove = max(msLargestTimeToMove, time);
    
    printInfo("moving id ");
    printInfo(id);
    printInfo(" from ");
    printInfo(curAngle);
    printInfo(" to ");
    printlnInfo(newAngle);

    Servos.setNextPose(id, newAngle);
  }
  
  printAck("Longest movement will take ");
  printAck(msLargestTimeToMove);
  printlnAck(" ms");
  
  Servos.interpolateSetup(round(msLargestTimeToMove));
}

// argument is number of angles to be transmitted
void cmdSetServoPositionBinary() {
  int numAngles = NumServos;

  if(char *arg = CmdMgr.next()) {
    int n;
    if(!toInt(arg, &n) || n < 1 || n > 127) {
      printAlways("Error: argument is number of servo angles to be sent, should be in [1, 127]. Assuming ");
      printlnAlways(NumServos);
    }
    else {
      numAngles = n;
    }
  }
  
  printAck("Expecting ");
  printAck(numAngles*2);
  printlnAck(" bytes");
  CmdMgr.enterBinaryMode(numAngles*2, setServoPositionBinary);
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
  Servos.setup(NumServos);
  
  // read in the position of each servo
  Servos.readPose();
  
  // Safe guard: the move interpolation code moves all servos, so if a servo starts
  // off-center, and we move another servo, the first servo will move to center (the default "next" position).
  // So set the target position of each servo to its current position
  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    Servos.setNextPose(id, Servos.getCurPose(id));
  }
  
  Serial.begin(38400);
  readVoltage();
  readServoPositions();
}

void loop() {
  if(Servos.interpolating) Servos.interpolateStep();
  CmdMgr.readSerial();
}


