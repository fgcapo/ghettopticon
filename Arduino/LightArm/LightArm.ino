#include <ax12.h>
#include <BioloidController.h>
#include <SerialCommand.h>

/////////////////////////////////////////////////////////////////////////////////
// globals

SerialCommand CmdMgr;

const int MAX_SERVOS = AX12_MAX_SERVOS;
BioloidController Servos(1000000);

// When a move is requestsudo udevadm trigger --action=changeed, the servos will move at different speeds in order to arrive
// at the target position simultaneously. No servo will move faster than this speed.
float gMaxSpeed = .5;  // "servo angle units" per ms

/////////////////////////////////////////////////////////////////////////////////////////////
// helpers

// returns false if str contains any characters other than numbers
boolean toDouble(const char *str, double *result) {
  char *end;
  if(*str == ' ') return false;
  *result = strtod(str, &end);

  // if end == str, str begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// returns false if str contains any characters other than numbers
boolean toLong(const char *str, long *result) {
  char *end;
  if(*str == ' ') return false;
  *result = strtol(str, &end, 10);
  
  // if end == str, str begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// returns false if str contains any characters other than numbers
boolean toInt(const char *str, int *result) {
  char *end;
  if(*str == ' ') return false;
  long r = strtol(str, &end, 10);
  
  // TODO check if out of int range
  *result = r;
  
  // if end == str, str begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

/*
// any whitespace encountered returns false
boolean isNumeric(const char *s, boolean canBeNegative=false, boolean canHavePeriod=false) {
  char c;
  boolean seenPeriod = false;
  
  //accept an initial negative sign
  if(canBeNegative && *s == '-') s++;
  
  while((c = *s++) != '\0') {
    if(c >= '0' && c <= '9') ;
    else if(canHavePeriod && !seenPeriod && c == '.') {
      seenPeriod = true;
    }
    else return false;
  }
  
  return true;
}*/

//////////////////////////////////////////////////////////////////////////////////
// commands
void cmdUnrecognized(const char *cmd) {
  Serial.println("unrecognized command");
}

// if no argument, prints the maximum speed
// if an argument given, sets the maximum speed and then prints it
// TODO clarify what units are! (angle unit per ms)
void cmdSetMaxSpeed() {
  if(char *arg = CmdMgr.next()) {
    //Serial.println("Error: takes one argument <speed in units per ms>");
  
    double speed;
    if(!toDouble(arg, &speed) || speed <= 0 || speed > 10) {
      Serial.println("Error: maxSpeed must be a number less than 10");
      return;
    }
    
    gMaxSpeed = speed;
  }
  
  Serial.print("speed ");
  Serial.println(gMaxSpeed);
}

//servo serial command format:
//"s <id>:<angle> <id>:<angle> ... \n"
//angle is 0 to 1024?
void cmdSetServoPosition() {
  const char *FormatErrorMsg = "Error: takes pairs in the form <ID>:<angle>";
  
  const int maxAngles = MAX_SERVOS;
  int angles[maxAngles];	// array indexed by ID
  memset(angles, -1, maxAngles*sizeof(*angles));
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    int id, angle;

    char *sID = strtok(arg, ":");
    if(sID == NULL) {
      Serial.println(FormatErrorMsg);
      return;
    }
    if(!toInt(sID, &id) || id < 1 || id > 127) {
      Serial.println("Error: ID must be between 1 and 127");
      return;
    }

    char *sAngle = strtok(NULL, ":");
    if(sAngle == NULL) {
      Serial.println(FormatErrorMsg);
      return;
    }
    //contrain from -90 to 90 degrees
    if(!toInt(sAngle, &angle) || angle < 200 || angle > 824) {
      Serial.println("Error: angle must be between 200 and 824");
      return;
    }
    
    angles[id] = angle;
    count++;
  }
  
  if(count == 0) {
    Serial.println("Error: no arguments");
    return;
  }

  float msLargestTimeToMove = 0;
  for(int i = 0; i < maxAngles; i++) {
    if(angles[i] == -1) continue;
    
    int curAngle = Servos.getCurPose(i);
    float time = abs(curAngle - angles[i]) / gMaxSpeed;
    msLargestTimeToMove = max(msLargestTimeToMove, time);
    
    /*Serial.print("moving id ");
    Serial.print(i);
    Serial.print(" from ");
    Serial.print(curAngle);
    Serial.print(" to ");
    Serial.println(angles[i]);*/

    Servos.setNextPose(i, angles[i]);
  }
  
  Serial.print("Longest movement will take ");
  Serial.print(msLargestTimeToMove);
  Serial.println(" ms");
  
  Servos.interpolateSetup(round(msLargestTimeToMove));
}

void readServoPositions() {
  for(int i = 0; i < Servos.poseSize; i++) {
    int id = Servos.getId(i);
    Serial.print("ID: ");
    Serial.print(id);
    Serial.print(" pos: ");
    Serial.println(Servos.getCurPose(id));
  }
}

void setup() {
  Servos.setup(4);
  Servos.readPose();
  float voltage = (ax12GetRegister (1, AX_PRESENT_VOLTAGE, 1)) / 10.0; 

  CmdMgr.setDefaultHandler(   cmdUnrecognized);
  CmdMgr.addCommand("s",      cmdSetServoPosition);
  CmdMgr.addCommand("r",      readServoPositions);
  CmdMgr.addCommand("speed",  cmdSetMaxSpeed);
  
  Serial.begin(9600);
  
  if(voltage < 0) {
    Serial.println("Dynamixel error: system reported voltage error. May be servos with duplicate IDs.");
  }
  else {
    Serial.print("Dynamixel ready. System voltage: ");
    Serial.print(voltage);
    Serial.println("V");
  }

  readServoPositions();
}

void loop() {
  CmdMgr.readSerial();
  if(Servos.interpolating) Servos.interpolateStep();
}


