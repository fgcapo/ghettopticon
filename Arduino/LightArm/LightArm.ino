#include <ax12.h>
#include <BioloidController2.h>    // use the bug-fixed version 
#include <PrintLevel.h>
#include <SC.h>

// this flag will invert PWM output (255-output), for active low devices
#define INVERT_HIGH_AND_LOW

/////////////////////////////////////////////////////////////////////////////////
// globals

struct PositionTuple { int id, angle; };

int parseID(const char *arg);
int parseAngle(const char *arg);
boolean parsePositionTuple(char *s, PositionTuple *out);
int parseListOfIDs(int *outIDs, int maxIDs);

void readVoltage();
void readServoPositions();
void cmdSetPrintLevel();
//void cmdSetMaxSpeed();
void cmdLoadPose();
void cmdMoveServos();
void cmdInterpolateServos();
void cmdInterpolateServosBinary();
void cmdRelax();
void cmdTorque();

SerialCommand::Entry CommandsList[] = {
  {"v",      readVoltage},
  {"r",      readServoPositions},
  {"plevel", cmdSetPrintLevel},
//  {"speed",  cmdSetMaxSpeed},
  {"p",      cmdLoadPose},
  {"s",      cmdMoveServos},
//  {"i",      cmdInterpolateServos},
//  {"B",      cmdInterpolateServosBinary},
  {"relax",  cmdRelax},
  {"torq",   cmdTorque},
  {"pwm",    cmdPWMPins},
  {NULL,     NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);

const int PWMPins[] = {12, 13, 14, 15};
const int NumPWMPins = sizeof(PWMPins)/sizeof(*PWMPins);

const int NumServos = 32;
BioloidController Servos(1000000);

const int BroadcastID = 254;

// When moving servos without interpolating, set this speed on the servos.
// The units are servo specific, range [1-1023].
int gServoSpeed = 80;

// When an interpolating move is requested, the servos will move at different speeds in order to
// arrive at the target position simultaneously. But movement time will be constrained so that
// servos will not violaten this maximum speed, constrained to [1-1000] angle-units per second
int gMaxInterpolationSpeed = 100;
// Speed is inverted to simplify calculation.
//int gMaxInterpolationSpeedInv = 10;  // max servo movement speed inverted, in ms per angle-unit

//bool relaxed = false;

const char *MsgTupleFormatError = "Error: takes pairs in the form <ID>:<angle>";

void broadcastSpeed() {
  ax12SetRegister2(BroadcastID, AX_GOAL_SPEED_L, gServoSpeed);
}

/*
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
*/

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns 0 if there is a parse error or the ID is out of range.
int parseID(const char *arg) {
  char *end;
  int id = strtol(arg, &end, 10);

  if(*end != '\0' || id < 1 || id > 253) {
      printlnError("Error: ID must be between 1 and 253");
      return 0;
  }
  
  return id;
}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns 0 if there is a parse error or the angle is out of range.
// Contrains from -90 to 90 degrees
int parseAngle(const char *arg) {
  char *end;
  int angle = strtol(arg, &end, 10);
  
  if(*end != '\0' || angle < 200 || angle > 824) {
    printlnError("Error: angle must be between 200 and 824");
    return 0;
  }
  
  return angle;
}

// convert "<id>:<angle>" into 2 integers in a struct
// returns false on error
boolean parsePositionTuple(char *s, PositionTuple *out) {
  char *sID = strtok(s, ":");
  if(sID == NULL) {
    printlnError(MsgTupleFormatError);
    return false;
  }
  
  int id = parseID(sID);
  if(id == 0) return false;

  char *sAngle = strtok(NULL, ":");
  if(sAngle == NULL) {
    printlnError(MsgTupleFormatError);
    return false;
  }
  
  int angle = parseAngle(sAngle);
  if(angle == 0) return false;
  
  out->id = id;
  out->angle = angle;
  return true;
}

// parse a list of IDs from CmdMgr into an array
// returns -1 on error
int parseListOfIDs(int *outIDs, int maxIDs) {
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= maxIDs) {
      printlnError("Error: too many IDs");
      return -1;
    }
    
    int id = parseID(arg);
    if(id == 0) return -1;
    outIDs[count++] = id;
  }
  
  return count;
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

// Relax a list of servos, or all if no arguments
void cmdRelax() {
  const int maxAngles = NumServos;
  int ids[maxAngles];
  
  int count = parseListOfIDs(ids, maxAngles);
  if(count == -1) return;
  
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
  
  int count = parseListOfIDs(ids, maxAngles);
  if(count == -1) return;
  
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

/*
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
    
    gMaxInterpolationSpeed = (int)(1000.0 / speed);  // convert to ms per angle-unit
  }
  
  printAck("max speed in angle-units per second: ");
  printlnAck(1000.0 / gMaxInterpolationSpeed);  // convert to angle-units per second
}*/

void readServoPositions() {
  printAck("Servo Readings:");
  //printlnAck(NumServos);
  
  //Servos.readPose();

  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    //int pos = Servos.getCurPose(id);
    int pos = Servos.readPose(i); //in case we've relaxed and some one manually moved the servos
    //Serial.println(pos);
    
    if(pos < 0 || pos > 1024) pos = 0;   // 8191-2 is invalid; replace with 0 because it's also invalid and shorter
    
    // print key:value pairs space delimited, but column-aligned
    /*char buf[16];
    int ixEnd = sprintf(buf, "ID:%d", id);
    while(ixEnd < 5) buf[ixEnd++] = ' ';
    buf[ixEnd] = '\0';

    printAck(buf);
    printAck(" pos:");
    printlnAck(pos);*/
  }

  // python dictionary notation;
  // allocate 3 for {}\0, and 8 for each pos, though (4 + comma) should be max digits
  char dictBuf[3 + NumServos * (3+1+4+1)] = "{";
  int ix = 1;

  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    int pos = Servos.getCurPose(id);
    if(pos < 0 || pos > 1024) continue;

    ix += sprintf(dictBuf+ix, "%d:%d,", id, pos);
  }
  
  dictBuf[ix - 1] = '}';    //overwrite the final comma
  printlnAlways(dictBuf);
}


// arguments are index:angle pairs
void cmdMoveServos() {
  broadcastSpeed();    // servos can forget their speed, or may have reset since we booted
  
  PositionTuple tuple;
  int count = 0;
  
  // see what kind of arguments we have
  while(char *arg = CmdMgr.next()) {

    if(count >= NumServos) {
      printlnError("Too many arguments");
      return;
    }

    if(parsePositionTuple(arg, &tuple) == false) return;
    count++;
    
  /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // hack in microcontroller for now:
  // invert movement of servo 28
  if(tuple.id == 28) tuple.angle = 1024 - tuple.angle;
  /////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    Servos.setCurPose(tuple.id, tuple.angle);
  }
  
  Servos.writePose();
  Serial.print("Moving ");
  Serial.print(count);
  Serial.println(" servos.");
}

//servo serial command format:
//"s <id>:<angle> <id>:<angle> ... \n"
//angle is 0 to 1024? or 1 to 1023?
// We shall constrain the angle to 200 to 824, and assume and consider 0 a no-op.
void cmdInterpolateServos() {
#if 0
  const int maxAngles = NumServos;
  PositionTuple angles[maxAngles];
  int count = 0;
  
  // parse any number of "id:angle" pairs
  while(char *arg = CmdMgr.next()) {
    if(count >= maxAngles) {
      printlnError("Too many arguments");
      return;
    }

    if(parsePositionTuple(arg, angles + count) == false) return;
    count++;
  }
  
  if(count == 0) {
    printlnError("Error: no arguments");
    return;
  }
  
  /*if(relaxed) {
    relaxed = false;
    Servos.readPose();
  }*/

  long msLongest = 0;
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
  
  Servos.interpolateSetup(msLongest);
#endif
}

// Takes an array of packed servo positions. Position == 0 is no-op.
void interpolateServosBinary(char *buffer, int len) {
#if 0
  int numAngles = min(len/2, NumServos);
  long msLongest = 0;  // move time required by any move
  int maxSpeedInv = invertMaxSpeed();  // convert to ms per angle-unit to simplify calculation
  
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

    // do not calculate movement time for or move a servo if it is incommunicado 
    // or we don't know where it currently is
    if(curAngle < 1 || curAngle > 1024) continue;
    
    long time = abs(curAngle - newAngle) * maxSpeedInv;
    msLongest = max(msLongest, time);
    
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
  
  Servos.interpolateSetup(msLongest);
#endif
}

// argument is number of angles to be transmitted
void cmdInterpolateServosBinary() {
  int numAngles = NumServos;

  if(char *arg = CmdMgr.next()) {
    char *end;
    int n = strtol(arg, &end, 10);
    
    // keep going even if there's an error, because the host will probably send the data anyway?
    if(end != '\0' || n < 1 || n > 253) {
      printAlways("Error: argument is number of servo angles to be sent, should be in [1, 253]. Assuming ");
      printlnAlways(NumServos);
      //return;
    }
    else {
      numAngles = n;
    }
  }
  
  printAck("Expecting ");
  printAck(numAngles*2);
  printlnAck(" bytes");
  CmdMgr.enterBinaryMode(numAngles*2, interpolateServosBinary);
}


void loadPose(int pos = 512) {

  for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    Servos.setCurPose(id, pos);
  }

  broadcastSpeed();
  Servos.writePose();
  Serial.print("Moving servos to position: ");
  Serial.println(pos);
}

void cmdLoadPose() {
  int Positions[] = {490, 500, 512, 612, 712};
  int NumPositions = sizeof(Positions) / sizeof(*Positions);
  
  if(char *arg = CmdMgr.next()) {
    int index = *arg - '1';
    if(index < 0 || index >= NumPositions) return;
    loadPose(Positions[index]);
  }
}

// expects up to 6 space-delimited ints 0-255
void cmdPWMPins() {
  const char *SetPWMUsageMsg = "Error: takes up to 4 arguments between 0 and 255";

  int channelValues[NumPWMPins];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumPWMPins) {
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
    printInfo(PWMPins[count]);
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
    analogWrite(PWMPins[i], c);
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
  Servos.setup(NumServos);
  
  // read in the position of each servo
  Servos.readPose();
  
  // Safe guard: the move interpolation code moves all servos, so if a servo starts
  // off-center, and we move another servo, the first servo will move to center (the default "next" position).
  // So set the target position of each servo to its current position
  /*for(int i = 0; i < NumServos; i++) {
    int id = Servos.getId(i);
    Servos.setNextPose(id, Servos.getCurPose(id));
  }*/
  
  Serial.begin(38400);
  readVoltage();
  readServoPositions();
  
  loadPose();
}

void loop() {
  if(Servos.interpolating) Servos.interpolateStep();
  CmdMgr.readSerial();
}


