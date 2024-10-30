const uint8_t pwmPin = 9;  // PWM pin para el Timer 1
float pwmValue = 0;
const long maxPWMValue = 33000;
const long pwmToLift = 18000;

const float Kp = 3;
const float Ki = 0.5;
const float Kd = 0.1;

float distance = 0.0;
float reference = 0.0;
float maxDistance = 0.0;

float P, I, D, PID = 0;
float errorSum = 0.0;

float previousTime = 0;
float deltaTime = 0;

float previousError;
bool reset = false;
long antiWindupStart = 0;

void setup() {
  Serial.begin(115200);
  pinMode(pwmPin, OUTPUT);

  // Configurar Timer 1 para operar en modo Fast PWM de 16 bits
  TCCR1A = _BV(COM1A1) | _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);
  ICR1 = 0xFFFF;

  OCR1A = maxPWMValue;
  delay(2000);
}

void loop() {
  if (Serial.available() > 0) readFromSerial();
  computePID();
  OCR1A = distance;
}

void computePID() {
  float error = distance - reference;
  float derivativeError = deltaTime != 0 ? (error - previousError) / deltaTime : 0;

  P = Kp * error;
  D = Kd * derivativeError;

  errorSum += deltaTime != 0 ? error * deltaTime : 0;
  previousError = error;

  I = Ki * errorSum;

  PID = P + I + D;
  PID *= -1;
  PID = constrain(PID, 0, maxPWMValue);
  pwmValue = mapFloat(PID, 0, maxPWMValue, 20000, maxPWMValue);
}

void readFromSerial() {
  String read = Serial.readStringUntil('\n');
  if (read[0] == 'R') {
    reference = read.substring(1).toFloat();
  } else {
    distance = read.toFloat();
  }

  long currentTime = millis();
  deltaTime = (15 / 1000.0);
  previousTime = currentTime;
}

float mapFloat(float value, float fromLow, float fromHigh, float toLow, float toHigh) {
  return (value - fromLow) * (toHigh - toLow) / (fromHigh - fromLow) + toLow; 
}
