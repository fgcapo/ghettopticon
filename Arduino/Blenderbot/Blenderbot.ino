/*
 
 */
/*#include <NewPing.h>
#define TRIGGER_PIN  22
#define ECHO_PIN     22
#define MAX_DISTANCE 500
/
//NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);

float sspeed = 55;
float cspeed = 0;
unsigned char last; 
int turn_delay = 200; //delay used to smooth out driving
int cmax = 150; // max speed. no higher than 250
int cinterval = 10; // speed increase / decrease interval
int avoid_on = 0;
int avoid_speed=55; //Turning speed for object avoidence
int pingd = 50; //object detection distace
int avoidState = '0';
*/

// pins, right and left, A=forward and B=reverse
const int rALI = 6;
const int rBLI = 8;
const int lALI = 9;    // LED connected to digital pin 9
const int lBLI = 10;

const int MAX_SPEED = 100;
const int MOTOR_INC = 10;  // motor speed increment

// left and right motor settings
// positive is foward, negative is backwards
// TODO what are max values?
int speedLeft = 0;
int speedRight = 0;

void updateMotorValues() {

  // forward and back seem to be flipped?  
  speedLeft = constrain(speedLeft, -MAX_SPEED, MAX_SPEED);
  if (speedLeft >= 0) {
    analogWrite(lALI, 0);
    analogWrite(lBLI, speedLeft);
  }
  else {
    analogWrite(lALI, -speedLeft);
    analogWrite(lBLI, 0);
  }
  
  speedRight = constrain(speedRight, -MAX_SPEED, MAX_SPEED);
  if (speedRight >= 0) {
    analogWrite(rALI, 0);
    analogWrite(rBLI, speedRight);
  }
  else {
    analogWrite(rALI, -speedRight);
    analogWrite(rBLI, 0);
  }

  /*Serial.print(speedLeft);
  Serial.print('\t');
  Serial.println(speedRight);*/

}

void stopMotors() {
  speedLeft = speedRight = 0;
  updateMotorValues();    //likely redundant but can't hurt
}


void setup()  { 
  // we set all 4 control pins to output
  pinMode(rALI, OUTPUT);
  pinMode(rBLI, OUTPUT);
  pinMode(lALI, OUTPUT);
  pinMode(lBLI, OUTPUT); 
  // Lets start the serial
  Serial.begin(9600);
  Serial.println(" Welcome To the snobot controls"); 
  Serial.println("   Drive Safely!");
} 

const int HEARTBEAT_TIMEOUT = 100;  //milliseconds
unsigned long lastHeatBeatReceived = millis();

void heartBeatReceived() {
  lastHeatBeatReceived = millis();
}

void loop() {

  // check failsafe and stop motors if we haven't received a heart beat recently enough
  unsigned long now = millis();
  if (now > lastHeatBeatReceived + HEARTBEAT_TIMEOUT) {
    stopMotors();
  }
  
  // commands are 3 bytes long
  if (Serial.available() > 3) {
    char cmd = Serial.read();
    char val = Serial.read();    //only used in L and R
    char newline = Serial.read();
	
    switch(cmd) {
      case '~': heartBeatReceived(); break;
      case ' ': stopMotors(); break;

      case 'e': speedLeft  += MOTOR_INC; updateMotorValues(); break;
      case 'd': speedLeft  -= MOTOR_INC; updateMotorValues(); break;
      case 'u': speedRight += MOTOR_INC; updateMotorValues(); break;
      case 'h': speedRight -= MOTOR_INC; updateMotorValues(); break;
  
      case 'L': speedLeft = val;         updateMotorValues(); break;
      case 'R': speedRight = val;        updateMotorValues(); break;
  
      default: return;
    }
  }
}


/*
void help(){
  Serial.println(" Controls(All lower case):");
  Serial.println(" Stop       = q");
  Serial.println(" Forward    = w");
  Serial.println(" Backward   = s");
  Serial.println(" Left       = a");
  Serial.println(" Right      = d");
  Serial.println(" Speed-Up   = o");
  Serial.println(" Speed-Down = l");
  Serial.println(" Distance   = x"); 
  Serial.println(" Run_Demo   = t"); 
  Serial.println(" Help       = h");

  Serial1.println(" Controls(All CAPS):");
  Serial1.println(" Stop       = q");
  Serial1.println(" Forward    = w");
  Serial1.println(" Backward   = s");
  Serial1.println(" Left       = a");
  Serial1.println(" Right      = d");
  Serial1.println(" Speed-Up   = o");
  Serial1.println(" Speed-Down = l"); 
  Serial1.println(" Distance   = x"); 
  Serial1.println(" Run_Demo   = t"); 
  Serial1.println(" Help       = h");
}*/


