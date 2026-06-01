/*
Nombre del proyecto: Servidor IoT con ESP32 y comunicación TCP/IP
Autor: Manganiello Maximiliano
Fecha: 31/05/2026

Descripción:
Este programa implementa un dispositivo IoT servidor utilizando
una placa NodeMCU-32S basada en el microcontrolador ESP32.

El sistema establece una conexión WiFi y pone en funcionamiento
un servidor TCP que permite recibir comandos remotos desde un
cliente desarrollado en Python. A través de dichos comandos es
posible consultar información proveniente de sensores así como
controlar actuadores.
*/

#include <WiFi.h>
#include <DHT.h>

// Configuración del sensor DHT11
const int DHTPIN = 4;
#define DHTTYPE DHT11

// Configuración de actuadores y sensores
const int LED_PIN = 2;
const int BUZZER_PIN = 22;
const int LDR_PIN = 34;

// Credenciales de la red WiFi
const char *ssid = "Nombre_WiFi";
const char *password = "Contraseña_Wifi";

// Configuración de red
IPAddress local_IP(192,168,100,200);
IPAddress gateway(192,168,100,1);
IPAddress subnet(255,255,255,0);

// Servidor TCP en puerto 80
WiFiServer server(80);

// Inicialización del sensor DHT11
DHT dht(DHTPIN, DHTTYPE);

void setup() {

  Serial.begin(115200);

  // Configuración de pines
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  dht.begin();

  // Configuración de IP fija
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Error configurando IP fija");
  }

  Serial.println("Conectando al WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Inicio del servidor TCP
  server.begin();

  Serial.println("Servidor TCP iniciado");
  Serial.println("Puerto: 80");
}

void loop() {

  // Espera la conexión de un cliente
  WiFiClient client = server.available();

  if (!client) {
    return;
  }

  Serial.println("Cliente conectado");

  while (client.connected()) {

    if (client.available()) {

      // Lectura del comando enviado por el cliente
      String cmd = client.readStringUntil('\n');
      cmd.trim();

      Serial.print("Comando recibido: ");
      Serial.println(cmd);

      // Control del LED
      if (cmd == "LED_ON") {

        digitalWrite(LED_PIN, HIGH);
        client.println("OK");
        client.println("END");

      } else if (cmd == "LED_OFF") {

        digitalWrite(LED_PIN, LOW);
        client.println("OK");
        client.println("END");

      // Control del buzzer
      } else if (cmd == "BUZZER_ON") {

        digitalWrite(BUZZER_PIN, HIGH);
        client.println("OK");
        client.println("END");

      } else if (cmd == "BUZZER_OFF") {

        digitalWrite(BUZZER_PIN, LOW);
        client.println("OK");
        client.println("END");
      
      // Lectura de temperatura
      } else if (cmd == "TEMP") {

        float t = dht.readTemperature();
        client.println(String(t));
        client.println("END");

      // Lectura de humedad
      } else if (cmd == "HUM") {

        float h = dht.readHumidity();
        client.println(String(h));
        client.println("END");

      // Lectura de luminosidad
      } else if (cmd == "LIGHT") {

        client.println(String(analogRead(LDR_PIN)));
        client.println("END");

      // Comando de ayuda
      } else if (cmd == "HELP") {

        client.println("LED_ON -> Enciende LED");
        client.println("LED_OFF -> Apaga LED");
        client.println("BUZZER_ON -> Enciende buzzer");
        client.println("BUZZER_OFF -> Apaga buzzer");
        client.println("TEMP -> Lee temperatura");
        client.println("HUM -> Lee humedad");
        client.println("LIGHT -> Lee luminosidad");
        client.println("END");

      }else {

        client.println("UNKNOWN_COMMAND");
        client.println("END");
      }
    }

    delay(10);
  }

  client.stop();

  Serial.println("Cliente desconectado");
}