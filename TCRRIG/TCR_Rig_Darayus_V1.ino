//For TCR Rig Rev 01

#include <elapsedMillis.h>

#define GOM_SAMPLE_RATE 1000

// Define pinout
//Muxes
#define Mux1_En 11  // Digital pin 11 controls Mux1 Enable
#define Mux1_A  10  // Digital pin 10 controls Mux1 A
#define Mux1_B  9   // Digital pin 9 controls Mux1 B

#define Mux2_En 8   // Digital pin 8 controls Mux2 Enable
#define Mux2_A  7   // Digital pin 7 controls Mux2 A
#define Mux2_B  6   // Digital pin 6 controls Mux2 B

//SSRs
#define SSR_1   12  // Digital pin 12 controls SSR for DUT 1
#define SSR_2   13  // Digital pin 13 controls SSR for DUT 2
#define SSR_3   A0  // Analog pin A0 controls SSR for DUT 3
#define SSR_4   A1  // Analog pin A1 controls SSR for DUT 4
#define SSR_5   A2  // Analog pin A2 controls SSR for DUT 5
#define SSR_6   A3  // Analog pin A3 controls SSR for DUT 6
#define SSR_7   A4  // Analog pin A4 controls SSR for DUT 7
#define SSR_8   A5  // Analog pin A5 controls SSR for DUT 8
byte SSRPins[] = {SSR_1, SSR_2, SSR_3, SSR_4, SSR_5, SSR_6, SSR_7, SSR_8};
//byte SSRPins[] = {SSR_8, SSR_7, SSR_6, SSR_5, SSR_4, SSR_3, SSR_2, SSR_1};

//Global Variables
elapsedMillis inDevice = 0;
elapsedMillis gom_measure_time = 0;
int ohmRange;
int deviceIndex;
int counter = 1;
int currentDUT;
int numDevices = 1;

//Serial1 command variables
boolean isWriting = false;
char fast_cmd[17] = "SENSe:SPEed FAST";
char slow_cmd[17] = "SENSe:SPEed SLOW";
char clear_cmd[5] = "*CLS";
char func_cmd[19] = "SENSe:FUNCtion OHM";
char read_cmd[5] = "READ?";
char speed_cmd[13] = "SENSe:SPEed?";
char range_cmd[20] = "SENSe:RANGe ";
char gom_cmd[50] = {};
char *gom_cmd_ptr;
double resistance;

// Serial command variables
char cmd_stream[7] = "stream";
char cmd_mode[5] = "mode";
char cmd_manual[4] = "man";
char cmd_man_home[5] = "home";
char cmd_man_max[4] = "max";
char cmd_man_cal[8] = "cal_man";
char cmd_auto_cal[9] = "cal_auto";
char cmd_start[6] = "start";
char cmd_stop[5] = "stop";
char cmd_kp_set[4] = "kp";
char cmd_ki_set[4] = "ki";
char cmd_kd_set[4] = "kd";

char cmd_one[4] = "one";
char cmd_two[4] = "two";
char cmd_three[4] = "thr";
char cmd_four[4] = "fou";
char cmd_five[4] = "fiv";
char cmd_six[4] = "six";
char cmd_seven[4] = "sev";
char cmd_eight[4] = "eig";

char ser_cmd[50] = {};
char *ser_cmd_ptr;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial1.begin(115200);
  pinMode(SSR_1, OUTPUT);
  pinMode(SSR_2, OUTPUT);
  pinMode(SSR_3, OUTPUT);
  pinMode(SSR_4, OUTPUT);
  pinMode(SSR_5, OUTPUT);
  pinMode(SSR_6, OUTPUT);
  pinMode(SSR_7, OUTPUT);
  pinMode(SSR_8, OUTPUT);
  pinMode(Mux1_En, OUTPUT);
  pinMode(Mux1_A, OUTPUT);
  pinMode(Mux1_B, OUTPUT);
  pinMode(Mux2_En, OUTPUT);
  pinMode(Mux2_A, OUTPUT);
  pinMode(Mux2_B, OUTPUT);
  inDevice = 0;
  deviceIndex = 0;

  memset(ser_cmd, 0, sizeof(ser_cmd));
  ser_cmd_ptr = &ser_cmd[0];

  memset(gom_cmd, 0, sizeof(gom_cmd));
  gom_cmd_ptr = &gom_cmd[0];

  delay(1000);

  currentDUT = 8;
  // Turn on Mux2 (it's low enable)
  digitalWrite(Mux2_En, LOW);

  // Set Mux2 to connect X, Y to X3, Y3
  digitalWrite(Mux2_A, HIGH);
  digitalWrite(Mux2_B, HIGH);

  digitalWrite(SSRPins[7], HIGH);

  gom_write(clear_cmd);
  gom_write(func_cmd);
  gom_write(fast_cmd);
}

//Disconnect all connections
void allOff() {
  // Turn off the Muxes (they're low enable)
  digitalWrite(Mux1_En, HIGH);
  digitalWrite(Mux2_En, HIGH);

  // Turn off the SSRs
  digitalWrite(SSR_1, LOW);
  digitalWrite(SSR_2, LOW);
  digitalWrite(SSR_3, LOW);
  digitalWrite(SSR_4, LOW);
  digitalWrite(SSR_5, LOW);
  digitalWrite(SSR_6, LOW);
  digitalWrite(SSR_7, LOW);
  digitalWrite(SSR_8, LOW);
}

bool string_compare(char *s1, char *s2) {
  while (*s1 != 0) {
    if (*s1 != *s2) {
      return false;
    }
    s1++;
    s2++;
  }
  return true;
}

// Serial Debug communication
void serial_listen(void) {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') {
      allOff();
      if (string_compare(cmd_eight, ser_cmd)) {
        currentDUT = 1;
        // Turn on Mux1 (it's low enable)
        digitalWrite(Mux1_En, LOW);

        // Set Mux1 to connect X, Y to X1, Y1
        digitalWrite(Mux1_A, HIGH);
        digitalWrite(Mux1_B, LOW);

        digitalWrite(SSRPins[0], HIGH);
      } else if (string_compare(cmd_seven, ser_cmd)) {
        currentDUT = 2;
        // Turn on Mux1 (it's low enable)
        digitalWrite(Mux1_En, LOW);

        // Set Mux1 to connect X, Y to X3, Y3
        digitalWrite(Mux1_A, HIGH);
        digitalWrite(Mux1_B, HIGH);

        digitalWrite(SSRPins[1], HIGH);
      } else if (string_compare(cmd_six, ser_cmd)) {
        currentDUT = 3;
        // Turn on Mux1 (it's low enable)
        digitalWrite(Mux1_En, LOW);

        // Set Mux1 to connect X, Y to X2, Y2
        digitalWrite(Mux1_A, LOW);
        digitalWrite(Mux1_B, HIGH);

        digitalWrite(SSRPins[2], HIGH);
      } else if (string_compare(cmd_five, ser_cmd)) {
        currentDUT = 4;
        // Turn on Mux1 (it's low enable)
        digitalWrite(Mux1_En, LOW);

        // Set Mux1 to connect X, Y to X0, Y0
        digitalWrite(Mux1_A, LOW);
        digitalWrite(Mux1_B, LOW);

        digitalWrite(SSRPins[3], HIGH);
      } else if (string_compare(cmd_four, ser_cmd)) {
        currentDUT = 5;
        // Turn on Mux2 (it's low enable)
        digitalWrite(Mux2_En, LOW);

        // Set Mux2 to connect X, Y to X0, Y0
        digitalWrite(Mux2_A, LOW);
        digitalWrite(Mux2_B, LOW);

        digitalWrite(SSRPins[4], HIGH);
      } else if (string_compare(cmd_three, ser_cmd)) {
        currentDUT = 6;
        // Turn on Mux2 (it's low enable)
        digitalWrite(Mux2_En, LOW);

        // Set Mux2 to connect X, Y to X0, Y0
        digitalWrite(Mux2_A, HIGH);
        digitalWrite(Mux2_B, LOW);

        digitalWrite(SSRPins[5], HIGH);
      } else if (string_compare(cmd_two, ser_cmd)) {
        currentDUT = 7;
        // Turn on Mux2 (it's low enable)
        digitalWrite(Mux2_En, LOW);

        // Set Mux2 to connect X, Y to X2, Y2
        digitalWrite(Mux2_A, LOW);
        digitalWrite(Mux2_B, HIGH);

        digitalWrite(SSRPins[6], HIGH);
      } else if (string_compare(cmd_one, ser_cmd)) {
        currentDUT = 8;
        // Turn on Mux2 (it's low enable)
        digitalWrite(Mux2_En, LOW);

        // Set Mux2 to connect X, Y to X3, Y3
        digitalWrite(Mux2_A, HIGH);
        digitalWrite(Mux2_B, HIGH);

        digitalWrite(SSRPins[7], HIGH);
      }
      memset(ser_cmd, 0, sizeof(ser_cmd));
      ser_cmd_ptr = &ser_cmd[0];
    }
    else {
      *ser_cmd_ptr++ = c;
    }
  }
}

void gom_write(char msg[]) {
  Serial1.write(msg);
  Serial1.write('\r');  // Carriage Return (EOL character)
}

void gom_listen(void) {
  if (Serial1.available()) {
    //Serial.print("Serial1 available");
    char c = Serial1.read();
    if (c == '\r') {
      //Serial.print(gom_cmd);
      //Serial.print(", ");
      //resistance = strtod(gom_cmd, NULL) ;
      resistance = (double)atof(gom_cmd);
      if (gom_measure_time >= GOM_SAMPLE_RATE) {
        Serial.print("Current DUT: ");
        Serial.print(currentDUT);
        Serial.print(",");
        Serial.print(millis()); //tImE sTaMp
        Serial.print(",");
        Serial.println(resistance, 4);
        gom_measure_time = 0;
      }
      memset(gom_cmd, 0, sizeof(gom_cmd));
      gom_cmd_ptr = &gom_cmd[0];
      isWriting = false;
      //delay(20);
    } else {
      //Serial.print(gom_cmd);
      *gom_cmd_ptr++ = c;
    }
  }
  //  else {
  //    //Serial.print("Serial1: no bytes available");
  //  }
}

void loop() {
  if (!isWriting) {
    gom_write(read_cmd);
    isWriting = true;
  }
  gom_listen();
  serial_listen();
  //
  //  if (inDevice >= 2000) {
  //    allOff();
  //    inDevice = 0;

  //    if (deviceIndex >= numDevices) {
  //      deviceIndex = 0;
  //    }
}
