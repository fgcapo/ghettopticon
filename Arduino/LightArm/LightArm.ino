#include <ax12.h>
#include <BioloidController2.h>    // use the bug-fixed version 
#include <SerialCommand.h>

/////////////////////////////////////////////////////////////////////////////////
// globals

SerialCommand CmdMgr;

BioloidController Servos(1000000);

// When a move is requestsudo udevadm trigger --action=changeed, the servos will move at different speeds in order to arrive
// at the target position simultaneously. No servo will move faster than this speed.
float gMaxSpeed = .5;  // "servo angle units" per ms

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
  Serial.println("unrecognized command");
}

// if no argument, prints the maximum speed
// if one argument, sets the maximum speed and then prints it
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
  
  if(CmdMgr.next()) {
    Serial.println("Error: takes 1 argument");
  }
  
  Serial.print("speed ");
  Serial.println(gMaxSpeed);
}

//servo serial command format:
//"s <id>:<angle> <id>:<angle> ... \n"
//angle is 0 to 1024?
void cmdSetServoPosition() {
  const char *FormatErrorMsg = "Error: takes pairs in the form <ID>:<angle>";

  struct Tuple { int id, angle; };
  
  const int maxAngles = Servos.poseSize;
  Tuple angles[maxAngles];
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
    
    angles[count].id = id;
    angles[count].angle = angle;
    count++;
  }
  
  if(count == 0) {
    Serial.println("Error: no arguments");
    return;
  }

  float msLargestTimeToMove = 0;
  for(int i = 0; i < count; i++) {
    int id = angles[i].id;
    int newAngle = angles[i].angle;
    int curAngle = Servos.getCurPose(id);
    
    float time = abs(curAngle - newAngle) / gMaxSpeed;
    msLargestTimeToMove = max(msLargestTimeToMove, time);
    
    /*Serial.print("moving id ");
    Serial.print(id);
    Serial.print(" from ");
    Serial.print(curAngle);
    Serial.print(" to ");
    Serial.println(newAngle);*/

    Servos.setNextPose(id, newAngle);
  }
  
  Serial.print("Longest movement will take ");
  Serial.print(msLargestTimeToMove);
  Serial.println(" ms");
  
  Servos.interpolateSetup(round(msLargestTimeToMove));
}

void readServoPositions() {
  char buf[16];
  for(int i = 0; i < Servos.poseSize; i++) {
    int id = Servos.getId(i);
    sprintf(buf, "%2d", id);
    Serial.print("ID: ");
    Serial.print(buf);
    Serial.print(" pos: ");
    Serial.println(Servos.getCurPose(id));
  }
}

void readVoltage() {
  float voltage = (ax12GetRegister (1, AX_PRESENT_VOLTAGE, 1)) / 10.0; 
  if(voltage < 0) {
    Serial.println("Dynamixel error: system reported voltage error. May be servos with duplicate IDs.");
  }
  else {
    Serial.print("Dynamixel ready. System voltage: ");
    Serial.print(voltage);
    Serial.println("V");
  }
}

void setup() {
  Servos.setup(32);
  
  // read in the position of each servo
  Servos.readPose();
  
  // Safe guard: the move interpolation code moves all servos, so if a servo starts
  // off-center, and we move another servo, the first servo will move to center (the default "next" position).
  // So set the target position of each servo to its current position
  for(int i = 0; i < Servos.poseSize; i++) {
    int id = Servos.getId(i);
    Servos.setNextPose(id, Servos.getCurPose(id));
  }

  CmdMgr.setDefaultHandler(   cmdUnrecognized);
  CmdMgr.addCommand("v",      readVoltage);
  CmdMgr.addCommand("r",      readServoPositions);
  CmdMgr.addCommand("s",      cmdSetServoPosition);
  CmdMgr.addCommand("speed",  cmdSetMaxSpeed);
  
  Serial.begin(9600);
  
  delay(1000);
  readVoltage();
  readServoPositions();
}

void loop() {
  CmdMgr.readSerial();
  if(Servos.interpolating) Servos.interpolateStep();
}


