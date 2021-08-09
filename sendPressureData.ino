#include <Wire.h>

int i2cAddresse = 0x40; // Adresse des Bus
int druckWert;          // Messwert des Drucks
int pinDruckEingang;    // analoger Eingangs-Pin

void setup()
{
  Wire.begin(i2cAddresse);            // I2C-Bus beitreten
  Wire.onRequest(requestEvent);       // Festlegen was bei Request passiert
  pinDruckEingang = A0;               // Eingangspin festlegen
  druckWert = 0;                      // druckWert initialisieren um Fehler zu vermeiden
  analogReference(DEFAULT);           // 5 V als Referenzspannung festlegen
}


void loop()
{
  druckWert = analogRead(pinDruckEingang);  // Auslesen des analogen Pins
  delay(5);                                 // Warten für 5 ms
}


void requestEvent()
{
  Wire.write(lowByte(druckWert));        // zuerst niedriges Byte schicken...
  Wire.write(highByte(druckWert));       // ...dann hohes Byte schicken
}