//For TCR Rig Rev 01

#include <elapsedMillis.h>

#define CHANNEL_TIMEOUT         500

// Define pinout
//Muxes
#define Mux1_En 11  // Digital pin 11 controls Mux1 Enable
#define Mux1_A  10  // Digital pin 10 controls Mux1 A
#define Mux1_B  9   // Digital pin 9 controls Mux1 B

#define Mux2_En 8   // Digital pin 8 controls Mux2 Enable
#define Mux2_A  7   // Digital pin 7 controls Mux2 A
#define Mux2_B  6   // Digital pin 6 controls Mux2 B

//SSRs
#define SSR_1   A5  // Analog pin A5 controls SSR for DUT 1
#define SSR_2   A4  // Analog pin A4 controls SSR for DUT 2
#define SSR_3   A3  // Analog pin A3 controls SSR for DUT 3
#define SSR_4   A2  // Analog pin A2 controls SSR for DUT 4
#define SSR_5   A1  // Analog pin A1 controls SSR for DUT 5
#define SSR_6   A0  // Analog pin A0 controls SSR for DUT 6
#define SSR_7   13  // Digital pin 13 controls SSR for DUT 7
#define SSR_8   12  // Digital pin 12 controls SSR for DUT 8

//Global Variables
elapsedMillis channel_sw_time;
elapsedMillis channel_read_time;

//Serial1 command variables (GOM-804 protocol)
char READ_QUERY[6] = "READ?";
char SPEED_QUERY[10] = "SENS:SPE?";
char GOM_INIT_AUTO[13] = "SENS:AUT OFF";
char GOM_INIT_RANGE[20] = "SENS:RANG 2";
char GOM_INIT_SPEED[14] = "SENS:SPE FAST";
char GOM_INIT_FUNC[14] = "SENS:FUNC OHM";
char CLEAR_STATUS[5] = "*CLS";

char gom_query[50] = {};
char *gom_query_ptr;

char print_string[120] = {};
char *print_ptr;

bool ch_read_flag;
bool query_flag;
bool print_flag;

// Serial command variables
char cmd_dut[4] = "dut";

char ser_cmd[50] = {};
char *ser_cmd_ptr;

enum channels {
  CHANNEL_1,
  CHANNEL_2,
  CHANNEL_3,
  CHANNEL_4,
  CHANNEL_5,
  CHANNEL_6,
  CHANNEL_7,
  CHANNEL_8,
  CHANNEL_TOTAL_NUM
};

int current_channel;
double resistance[CHANNEL_TOTAL_NUM];

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

  memset(ser_cmd, 0, sizeof(ser_cmd));
  ser_cmd_ptr = &ser_cmd[0];

  memset(gom_query, 0, sizeof(gom_query));
  gom_query_ptr = &gom_query[0];

  memset(print_string, 0, sizeof(print_string));
  print_ptr = &print_string[0];

  memset(resistance, 0, sizeof(resistance));

  // Enable channel 1
  current_channel = CHANNEL_1;
  enable_channel(current_channel);

  // Setup GOM-804
  gom_write(CLEAR_STATUS);
  gom_write(GOM_INIT_FUNC);
  gom_write(GOM_INIT_SPEED);
  gom_write(GOM_INIT_AUTO);
  gom_write(GOM_INIT_RANGE);

  ch_read_flag = false;
  query_flag = false;
  print_flag = false;

  channel_sw_time = 0;
  channel_read_time = 0;
}

void loop() {
  gom_check();
  serial_listen();
  print_data();
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

void enable_channel(int ch) {
  allOff();
  delay(100);
  switch (ch) {
    case CHANNEL_1:
      digitalWrite(SSR_1, HIGH);
      digitalWrite(Mux2_En, LOW);

      digitalWrite(Mux2_A, HIGH);
      digitalWrite(Mux2_B, HIGH);      
      break;
    case CHANNEL_2:
      digitalWrite(SSR_2, HIGH);
      digitalWrite(Mux2_En, LOW);
      
      digitalWrite(Mux2_A, LOW);
      digitalWrite(Mux2_B, HIGH); 
      break;
    case CHANNEL_3:
      digitalWrite(SSR_3, HIGH);
      digitalWrite(Mux2_En, LOW);
      
      digitalWrite(Mux2_A, HIGH);
      digitalWrite(Mux2_B, LOW); 
      break;
    case CHANNEL_4:
      digitalWrite(SSR_4, HIGH);
      digitalWrite(Mux2_En, LOW);
      
      digitalWrite(Mux2_A, LOW);
      digitalWrite(Mux2_B, LOW); 
      break;
    case CHANNEL_5:
      digitalWrite(SSR_5, HIGH);
      digitalWrite(Mux1_En, LOW);
      
      digitalWrite(Mux1_A, LOW);
      digitalWrite(Mux1_B, LOW); 
      break;
    case CHANNEL_6:
      digitalWrite(SSR_6, HIGH);
      digitalWrite(Mux1_En, LOW);
      
      digitalWrite(Mux1_A, LOW);
      digitalWrite(Mux1_B, HIGH); 
      break;
    case CHANNEL_7:
      digitalWrite(SSR_7, HIGH);
      digitalWrite(Mux1_En, LOW);
      
      digitalWrite(Mux1_A, HIGH);
      digitalWrite(Mux1_B, HIGH); 
      break;
    case CHANNEL_8:
      digitalWrite(SSR_8, HIGH);
      digitalWrite(Mux1_En, LOW);
      
      digitalWrite(Mux1_A, HIGH);
      digitalWrite(Mux1_B, LOW); 
      break;
  }
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
      // if (string_compare(cmd_eight, ser_cmd)) {

      // } 
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
    char c = Serial1.read();
    if (c == '\r') {
      resistance[current_channel] = (double)atof(gom_query);
      gom_query_ptr = &gom_query[0];
      while (*gom_query_ptr != '\0') {
        *print_ptr++ = *gom_query_ptr;
        gom_query_ptr++;
      }
      *print_ptr++ = ',';
      ch_read_flag = true;
      memset(gom_query, 0, sizeof(gom_query));
      gom_query_ptr = &gom_query[0];
    } else {
      *gom_query_ptr++ = c;
    }
  }
}

void gom_check(void) {
  if (channel_sw_time >= (CHANNEL_TIMEOUT >> 1) && !query_flag) {
    gom_write(READ_QUERY);
    query_flag = true;
  }
  else if ((channel_sw_time >= CHANNEL_TIMEOUT) && ch_read_flag) {
    channel_sw_time = 0;
    ch_read_flag = false;
    query_flag = false;
    if (++current_channel >= CHANNEL_TOTAL_NUM) {
      current_channel = CHANNEL_1;
      print_flag = true;
    }
    enable_channel(current_channel);
  }
  gom_listen();
}

void print_data(void) {
  if (print_flag) {
    print_flag = false;
    *(--print_ptr) = '\r';    // overwrite last ',' in string
    print_ptr++;
    *print_ptr++ = '\n';
    Serial.print(print_string);
    memset(print_string, 0, sizeof(print_string));
    print_ptr = &print_string[0];
  }
}
