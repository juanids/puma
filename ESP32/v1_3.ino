#include <Arduino.h>
#include <MCP492X.h>

// --- Estructuras para la Cola de Tareas ---
struct Tarea {
  char tipo;
  int p[16]; // Parámetros: M(5), I(6), P(9)
};

Tarea cola[100]; // Capacidad aumentada a 100 tareas
int totalTareas = 0;
bool modoSecuencia = false;
unsigned long t_cero_global = 0;

// --- Definiciones de Hardware ---
  #define SER 37       
  #define RCLK 36   
  #define SRCLK 47  
byte estados[8] = {34, 34, 34, 34, 34, 34, 34, 34};

const byte pin_sck  = 41; 
const byte pin_sdi  = 42;
const byte pin_cs   = 45; 
MCP492X mcp4922(pin_cs);

#define PIN_CONVST 17
#define PIN_RD     18
#define PIN_BUSY   21
#define PIN_RESET  38
#define PIN_CS_1   39
#define PIN_CS_2   40
#define RAGE   35
const uint32_t MASCARA_ADC = 0x1FFFE;
int16_t valores[16]; 

// --- Funciones de Hardware (Sin cambios) ---
void actualizarRegistros() {
  digitalWrite(RCLK, LOW);
  for (int i = 7; i >= 0; i--) shiftOut(SER, SRCLK, MSBFIRST, estados[i]);
  digitalWrite(RCLK, HIGH);
}

void LeerTodosADC() {
  GPIO.out_w1tc = (1 << PIN_CONVST);
  __asm__("nop");
  GPIO.out_w1ts = (1 << PIN_CONVST);
  while(GPIO.in & (1 << PIN_BUSY));
  digitalWrite(PIN_CS_1, LOW);
  for (int i = 0; i < 8; i++) {
    GPIO.out_w1tc = (1 << PIN_RD); __asm__("nop"); __asm__("nop");
    valores[i] = (int16_t)((GPIO.in & MASCARA_ADC) >> 1);
    GPIO.out_w1ts = (1 << PIN_RD);
  }
  digitalWrite(PIN_CS_1, HIGH);
  digitalWrite(PIN_CS_2, LOW);
  for (int i = 8; i < 16; i++) {
    GPIO.out_w1tc = (1 << PIN_RD); __asm__("nop"); __asm__("nop");
    valores[i] = (int16_t)((GPIO.in & MASCARA_ADC) >> 1);
    GPIO.out_w1ts = (1 << PIN_RD);
  }
  digitalWrite(PIN_CS_2, HIGH);
}

void SeleccionarCanal(int i, int j, int m) {
  int bI = i / 2;
  if(i<=7) {
    if (i % 2 == 0) { estados[bI] &= 0x20; estados[bI] |= m<<1; }
    else { estados[bI] &= 0x2; estados[bI] |= m<<5; }
  } else {
    if (i % 2 == 0) { estados[bI] &= 0x2; estados[bI] |= m<<5; }
    else { estados[bI] &= 0x20; estados[bI] |= m<<1; }
  }
  int bJ = j / 2;
  if(j<=7) { if (j % 2 == 0) estados[bJ] &= 0xF0; else estados[bJ] &= 0x0F; }
  else { if (j % 2 == 0) estados[bJ] &= 0x0F; else estados[bJ] &= 0xF0; }
  actualizarRegistros();
  delayMicroseconds(100);
}
void ReinicarCanales(){
for (int i = 0; i < 8; i++) {
  estados[i] = 0x22;
}
actualizarRegistros();
}

void Reiniciar(int i, int j) {
  estados[j/2] = 0x33; estados[i/2] = 0x22;
  actualizarRegistros();
}

// --- Rutinas de Medición (Actualizadas para usar parámetros del struct) ---
void Mapeo(int m, int v, int c, int d, int t) {
  if(v<2000){
    digitalWrite(RAGE, LOW);
  }
  else{
    digitalWrite(RAGE, HIGH);
  }
  unsigned long t_relativo_al_inicio = micros() - t_cero_global; 
  Serial.print("T_START_REL:"); Serial.println(t_relativo_al_inicio);
  Serial.println("READY_MAPEO");
  mcp4922.analogWrite(false, false, true, true, v);
  delayMicroseconds(20);
  LeerTodosADC();
  if (t==1){
    int16_t vaux[240];
    int16_t iaux[120];
    int16_t jaux[120];
    uint32_t taux[120];
    for (int ciclo = 0; ciclo < c; ciclo++) {
      
      int cont = 0;
      for (int i = 0; i < 16; i++) {
        for (int j = i + 1; j < 16; j++) {
          SeleccionarCanal(i, j, m); 
          LeerTodosADC();
          taux[cont] = micros() - t_cero_global;
          
          vaux[cont*2] = valores[i]; 
          vaux[cont*2+1] = valores[j];
          iaux[cont]=i;
          jaux[cont]=j;
          estados[i>>1] = 0x22; estados[j>>1] = 0x22; actualizarRegistros();
          cont++;
          
        }
      }
      
      for (int n = 0; n < 120; n++) {
        int16_t t_bajo = (int16_t)(taux[n] & 0xFFFF);
        int16_t t_alto = (int16_t)((taux[n] >> 16) & 0xFFFF);
        int16_t cs = vaux[n*2] + vaux[n*2+1] + iaux[n] + jaux[n] + t_bajo + t_alto;
        
        Serial.write((uint8_t*)&iaux[n], 2);
        Serial.write((uint8_t*)&jaux[n], 2);
        Serial.write((uint8_t*)&vaux[n*2], 2);
        Serial.write((uint8_t*)&vaux[n*2+1], 2);
        Serial.write((uint8_t*)&taux[n], 4); // <-- 4. Enviamos el tiempo global (4 bytes)
        Serial.write((uint8_t*)&cs, 2);
      }
      if (ciclo < c - 1 && d > 0) delayMicroseconds(d);
    }
  }
  
  mcp4922.analogWrite(false, false, true, true, 0);
  Serial.println("DONE_MAPEO");
  digitalWrite(RAGE, HIGH);
}

void determinarPines(int &in_idx, int &out_idx, int &in_count, int &out_count) {
  in_idx = -1; 
  out_idx = -1;
  in_count = 0; 
  out_count = 0;

  for (int ind = 0; ind < 8; ind++) {
    byte byte_actual = estados[ind];
    byte nibble_bajo = byte_actual & 0x0F;
    byte nibble_alto = (byte_actual >> 4) & 0x0F;

    int canal_A = ind * 2;       // Índice de 0 a 15
    int canal_B = ind * 2 + 1;   // Índice de 0 a 15

    byte val_A, val_B;
    if (canal_A < 8) { 
      val_A = nibble_bajo; 
      val_B = nibble_alto;
    } else {           
      val_A = nibble_alto; 
      val_B = nibble_bajo;
    }

    // Clasificar canal A
    if (val_A == 0) { in_idx = canal_A; in_count++; }
    else if (val_A != 2) { out_idx = canal_A; out_count++; }

    // Clasificar canal B
    if (val_B == 0) { in_idx = canal_B; in_count++; }
    else if (val_B != 2) { out_idx = canal_B; out_count++; }
  }
}

void IV(int v, int c, int d, int pulsos, int cota,int puntos,int pasos2) {
  if(v<2000){
    digitalWrite(RAGE, LOW);
  }
  else{
    digitalWrite(RAGE, HIGH);
  }

  unsigned long t_relativo_al_inicio = micros() - t_cero_global; 
  Serial.print("T_START_REL:"); Serial.println(t_relativo_al_inicio);
  int in_idx, out_idx, in_count, out_count;
  determinarPines(in_idx, out_idx, in_count, out_count);
  
  // Serial.print("DEBUG_PINS -> IN:"); Serial.print(in_idx); Serial.print(" | OUT:"); Serial.print(out_idx); Serial.print(" | CountIN:"); Serial.print(in_count); Serial.print(" | CountOUT:"); Serial.print(out_count);Serial.print(" | Cota:"); Serial.println(cota);


  Serial.println("READY");

  Serial.flush();        // 1. Forza a que se mande todo el texto antes de seguir [cite: 12]
  delayMicroseconds(50);
  // SeleccionarCanal(i, j, m);
  
  for (int ciclo = 0; ciclo < c; ciclo++) {
    unsigned long t_ref = micros();
    bool abortar = false; // Bandera para romper todos los ciclos
    for (int volt = 0; volt <= v; volt++) {
      if (abortar) break;
      for (int auxi=0; auxi<puntos; auxi++){
        if (abortar) break;
        mcp4922.analogWrite(false, false, true, true, volt);
        delayMicroseconds(20);
        unsigned long t_act = micros() - t_ref;
        LeerTodosADC();
        uint8_t ck = 0;
        Serial.write((uint8_t*)&t_act, 4);
        for (int k = 0; k < 16; k++) {
            
          ck += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
        }
        Serial.write(ck);
        if (in_count == 1 && out_count == 1 && volt > 200) {
          if (valores[out_idx] != 0) { // Prevenir división por cero
            float ratio = (float)abs(valores[in_idx]) / (float)abs(valores[out_idx]);
            // "Cuando la condición (ratio > cota) NO se cumpla, salir"
            if (!(ratio > cota)) {
              for (int p2 = 0; p2 < pasos2; p2++) {
                mcp4922.analogWrite(false, false, true, true, volt);
                delayMicroseconds(20);
                unsigned long t_act2 = micros() - t_ref;
                LeerTodosADC();
                uint8_t ck2 = 0;
                Serial.write((uint8_t*)&t_act2, 4);
                for (int k = 0; k < 16; k++) {
                  Serial.write((uint8_t*)&valores[k], 2);
                  ck2 += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
                }
                Serial.write(ck2);
              }
              abortar = true;
            }
          }
        }
      }  
    }
    if (!abortar) {
      mcp4922.analogWrite(false, false, true, true, v);
      for (int p = 0; p < pulsos; p++) {
        if (abortar) break;
        delayMicroseconds(20);
        unsigned long t_act = micros() - t_ref;
        LeerTodosADC();
        uint8_t ck = 0;
        Serial.write((uint8_t*)&t_act, 4);
        for (int k = 0; k < 16; k++) {
          Serial.write((uint8_t*)&valores[k], 2);
          ck += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
        }
        Serial.write(ck);
        if (in_count == 1 && out_count == 1 && v > 200) {
          if (valores[out_idx] != 0) {
            float ratio = (float)abs(valores[in_idx]) / (float)abs(valores[out_idx]);
            if (!(ratio > cota)) {
              for (int p2 = 0; p2 < pasos2; p2++) {
                mcp4922.analogWrite(false, false, true, true, v);
                delayMicroseconds(20);
                unsigned long t_act2 = micros() - t_ref;
                LeerTodosADC();
                uint8_t ck2 = 0;
                Serial.write((uint8_t*)&t_act2, 4);
                for (int k = 0; k < 16; k++) {
                  Serial.write((uint8_t*)&valores[k], 2);
                  ck2 += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
                }
                Serial.write(ck2);
              }
              abortar = true;
            }
          }
        }
      }
    }
    if (ciclo < c - 1 && d > 0) delayMicroseconds(d);
  }
  mcp4922.analogWrite(false, false, true, true, 0); 
  Serial.flush(); 
  delayMicroseconds(50);
  Serial.println("DONE_EXP"); // Usamos una etiqueta genérica
  digitalWrite(RAGE, HIGH);
}

void Aplpulsos( int v1, int c1, int v2, int c2, int c, int d) {
  if(v1<2000 && v2<2000){
    digitalWrite(RAGE, LOW);
  }
  else{
    digitalWrite(RAGE, HIGH);
  }
  unsigned long t_relativo_al_inicio = micros() - t_cero_global; 
  Serial.print("T_START_REL:"); Serial.println(t_relativo_al_inicio);
  Serial.println("READY");
  Serial.flush();        // 1. Forza a que se mande todo el texto antes de seguir [cite: 12]
  delayMicroseconds(50);
  unsigned long t_ref = micros();
  
  // SeleccionarCanal(i, j, m);
  for (int ciclo = 0; ciclo < c; ciclo++) {
    unsigned long t_ref = micros();
    mcp4922.analogWrite(false, false, true, true, v1);
    delayMicroseconds(20);
    for (int i = 0; i < c1; i++) {
      
      
      
      unsigned long t_act = micros() - t_ref;
      LeerTodosADC();
      uint8_t ck = 0;
      Serial.write((uint8_t*)&t_act, 4);
      for (int k = 0; k < 16; k++) {
        Serial.write((uint8_t*)&valores[k], 2);
        ck += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
      }
      Serial.write(ck);
    }
    mcp4922.analogWrite(false, false, true, true, v2);
    for (int i = 0; i < c2; i++) {
      
      
      delayMicroseconds(20);
      unsigned long t_act = micros() - t_ref;
      LeerTodosADC();
      uint8_t ck = 0;
      Serial.write((uint8_t*)&t_act, 4);
      for (int k = 0; k < 16; k++) {
        Serial.write((uint8_t*)&valores[k], 2);
        ck += ((uint8_t*)&valores[k])[0] + ((uint8_t*)&valores[k])[1];
      }
      Serial.write(ck);
    }
    if (ciclo < c - 1 && d > 0) delayMicroseconds(d);
  }
  mcp4922.analogWrite(false, false, true, true, 0); 
  Serial.flush(); 
  delayMicroseconds(50);
  Serial.println("DONE_EXP");
  digitalWrite(RAGE, HIGH);
}



// --- Lógica de la Secuencia ---
void ejecutarTarea(Tarea t) {
  if (t.tipo == 'M') Mapeo(t.p[0], t.p[1], t.p[2], t.p[3], t.p[4]);
  else if (t.tipo == 'I') {
    
    for (int i = 0; i < 8; i++) {
      estados[i] = (byte) t.p[i]; 
    }
    actualizarRegistros();
    
    IV(t.p[8], t.p[9], t.p[10], t.p[11], t.p[12], t.p[13],t.p[14]);
    for (int i = 0; i < 8; i++) {
      estados[i] = 0b00100010; 
    }
    actualizarRegistros();
  }

  else if (t.tipo == 'P') {
    
    for (int i = 0; i < 8; i++) {
      estados[i] = (byte) t.p[i]; 
    }
    actualizarRegistros();
    Aplpulsos(t.p[8], t.p[9], t.p[10], t.p[11], t.p[12], t.p[13]);
    for (int i = 0; i < 8; i++) {
      estados[i] = 0b00100010; 
    }
    actualizarRegistros();
  }
  
}
void imprimirTareaDiagnostico(Tarea t, int indice) {
  Serial.print("Tarea ["); Serial.print(indice); Serial.print("] Tipo: ");
  Serial.print(t.tipo);
  Serial.print(" | Params: ");
  for(int i = 0; i < 15; i++) {
    Serial.print(t.p[i]);
    if(i < 14) Serial.print(", ");
  }
  Serial.println();
}


void setup() {
 
   Serial.begin(921600);
  unsigned long start = millis();
  while (!Serial && (millis() - start < 3000));
  
  pinMode(SER, OUTPUT); pinMode(RCLK, OUTPUT); pinMode(SRCLK, OUTPUT);
  actualizarRegistros();
  pinMode(RAGE, OUTPUT);
  digitalWrite(RAGE, HIGH);
  SPI.begin(pin_sck, -1, pin_sdi, pin_cs); mcp4922.begin();
  pinMode(PIN_CONVST, OUTPUT); pinMode(PIN_RD, OUTPUT); pinMode(PIN_RESET, OUTPUT);
  pinMode(PIN_CS_1, OUTPUT); pinMode(PIN_CS_2, OUTPUT); pinMode(PIN_BUSY, INPUT);
  for (int i = 1; i <= 16; i++) pinMode(i, INPUT);
  digitalWrite(PIN_RESET, HIGH); delay(10); digitalWrite(PIN_RESET, LOW);
  mcp4922.analogWrite(false, false, true, true, 0);
  Serial.println("SISTEMA_READY");
}

void loop() {
 if (Serial.available() > 0) {
    String trama = Serial.readStringUntil('\n'); trama.trim();
    if (trama.length() == 0) return;
    char cmd = trama[0];

    if (cmd == 'Q') { totalTareas = 0; modoSecuencia = true; Serial.println("CONFIRM_QUEUE_CLEAR"); }
    else if (cmd == 'V') {
       Serial.println("PUMA v1.3");
    }
    else if (cmd == 'S') {
       ReinicarCanales();
      t_cero_global = micros(); // <--- PUNTO CERO: Momento del disparo
      Serial.print("T_GLOBAL_ZERO:"); Serial.println(t_cero_global);
      Serial.println("CONFIRM_START_SEQUENCE");
      for (int i = 0; i < totalTareas; i++) {
        ejecutarTarea(cola[i]);
        Serial.flush();
        delayMicroseconds(100);
      }
      Serial.println("ALL_DONE");
      modoSecuencia = false; 
      totalTareas = 0;
    }
    else if (totalTareas < 100) {
      Tarea &t = cola[totalTareas]; t.tipo = cmd;
      bool valida = false;
      if (cmd == 'M') valida = (sscanf(trama.c_str(), "M,%d,%d,%d,%d,%d", &t.p[0], &t.p[1], &t.p[2], &t.p[3], &t.p[4]) == 5);
      else if (cmd == 'I') valida = (sscanf(trama.c_str(), "I,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", &t.p[0], &t.p[1], &t.p[2], &t.p[3], &t.p[4], &t.p[5], &t.p[6], &t.p[7], &t.p[8], &t.p[9], &t.p[10], &t.p[11], &t.p[12], &t.p[13], &t.p[14]) == 15);
      else if (cmd == 'P') valida = (sscanf(trama.c_str(), "P,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", &t.p[0], &t.p[1], &t.p[2], &t.p[3], &t.p[4], &t.p[5], &t.p[6], &t.p[7], &t.p[8], &t.p[9], &t.p[10], &t.p[11], &t.p[12], &t.p[13]) == 14);
      
      if (valida) {
        if (modoSecuencia) { totalTareas++; Serial.println("CONFIRM_QUEUED"); }
        else {
          // Serial.flush();
          // delayMicroseconds(100);
          ejecutarTarea(t);
        }
      }
    }
  }
}