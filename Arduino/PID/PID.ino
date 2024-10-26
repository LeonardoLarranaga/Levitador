const uint8_t pwmPin = 9; // PWM pin para el Timer 1
long pwmValue = 0;
const long maxPWMValue = 65535;
const long pwmToLift = 18000;

const float Kp = 1.8;
const float Ki = 0.4;
const float Kd = 1.1;

float distance = 0.0;
float reference = 0.0;
float maxDistance = 0.0;

float P, I, D, PID;
float errorSum = 0.0;

unsigned long initialTime = 0;

unsigned long currentTime = 0, prevTime = 0;
float deltaTime = 0.0;

float previousError;
bool reset = false;

void setup() {
  Serial.begin(115200);
  pinMode(pwmPin, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  // Configurar Timer 1 para operar en modo Fast PWM de 16 bits
  TCCR1A = _BV(COM1A1) | _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);
  ICR1 = 0xFFFF;

  // Timer en máximo por 3 segundos, para que se obtenga una medición en Python...
  OCR1A = pwmToLift;
  delay(3000);  // Espera de 3 segundos

  OCR1A = 0;
}

void loop() {
  currentTime = millis();
  deltaTime = (currentTime - prevTime) / 1000.0;
  if (Serial.available() > 0) readFromSerial();
  computePID();
  OCR1A = pwmValue;
  prevTime = currentTime;
}

void computePID() {
  float error = distance - reference;
  float derivativeError = (error - previousError) / deltaTime;

  P = Kp * error;
  D = Kd * derivativeError;

  // if (abs(error) > (0.015 * reference)) {
  //   if (reset) {
  //     if (millis() - initialTime > 3000) {
  //       errorSum /= 5.0;
  //       reset = false;
  //     }
  //   } else {
  //     reset = true;
  //     initialTime = millis();
  //   }
  // } else if (abs(error) < (0.019 * reference)) reset = false;

  errorSum += error * deltaTime;
  previousError = error;

  I = Ki * errorSum;

  PID = P + I + D;
  PID *= -1;
  PID = constrain(PID, -maxPWMValue, maxPWMValue);
  PID = map(PID, -maxPWMValue, maxPWMValue, 10000.0, maxPWMValue);
  Serial.print("PID: ");
  Serial.println(PID);
  pwmValue = PID;
}

void readFromSerial() {
  String read = Serial.readStringUntil('\n');
  if (read[0] == 'R') {
    reference = read.substring(1).toFloat();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    Serial.print("Reference: ");
    Serial.println(reference);
  } else {
    distance = read.toFloat();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    // Serial.print("Distance: ");
    // Serial.println(distance);
  }
}