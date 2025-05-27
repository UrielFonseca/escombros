/*
  Arduino sketch to read sensor data and send it via serial.
  Modify the sensor pin and reading code as needed for your specific sensor.
*/

const int sensorPin = A0;  // Analog input pin for sensor

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(sensorPin);
  float voltage = sensorValue * (5.0 / 1023.0);

  // Send sensor value and voltage over serial in CSV format
  Serial.print(sensorValue);
  Serial.print(",");
  Serial.println(voltage);

  delay(1000);  // Send data every 1 second
}
