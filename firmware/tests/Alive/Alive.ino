void setup() { Serial.begin(115200); }
void loop() { Serial.printf("InspectPin alive millis=%lu heap=%u PSRAM=%u\n",millis(),ESP.getFreeHeap(),ESP.getPsramSize()); delay(1000); }
