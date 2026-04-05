#include <SPI.h>
#include <MFRC522.h>

const int RST_PIN = 7;
const int SS_PIN = 15;
const int CS_ACEL = 2;

const int SCK_PIN = 40;
const int MISO_PIN = 38;
const int MOSI_PIN = 39;

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  
  // Desactivar acelerómetro (HIGH = Desactivado en SPI)
  pinMode(CS_ACEL, OUTPUT);
  digitalWrite(CS_ACEL, HIGH);
  
  pinMode(SS_PIN, OUTPUT);
  digitalWrite(SS_PIN, HIGH);
  
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  mfrc522.PCD_Init();
  
  Serial.println("Lector listo. Acerque su tarjeta...");
}

void loop() {
  // 1. Buscamos si hay una tarjeta nueva presente
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return; // Si no hay tarjeta, salimos del loop y volvemos a empezar
  }

  // 2. Intentamos leer el Serial (UID) de esa tarjeta
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return; // Si detectó pero no pudo leer el UID, salimos
  }

  // 3. Si llegamos aquí, ¡tenemos el UID!
  Serial.print(F("Card UID:"));
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.println();

  // 4. Instrucción de parada para no leer la misma tarjeta 100 veces por segundo
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1(); // Importante para liberar el estado del lector
  
  delay(500); // Pequeña pausa antes de la siguiente lectura
}