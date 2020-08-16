#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <FastLED.h>
#include <ArduinoJson.h>

#ifndef STASSID
#define STASSID "NETGEAR30"
#define STAPSK "gentlecream139"
#endif

#define UDPPORT 8888

#define NUMLEDS 36
#define LEDPIN 7
#define DEVICENAME "RING1"

char packetBuffer[UDP_TX_PACKET_MAX_SIZE+1];

WiFiUDP Udp;
IPAddress broadcastIP;
char broadcastMsg[255];
CRGB leds[NUMLEDS];

int bcasttimer = 0;
unsigned long curTime;

void setup_serial(){
  Serial.begin(115200);
}

void setup_wifi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(STASSID, STAPSK);
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(500);
  }
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());
  Serial.printf("UDP server on port %d\n", UDPPORT);
  Udp.begin(UDPPORT);

  broadcastIP = ~(uint32_t)WiFi.subnetMask() | (uint32_t)WiFi.gatewayIP();
  sprintf(broadcastMsg, "{\"name\":\"%s\", \"address\": \"%s\", \"type\": \"ring\"}", DEVICENAME, WiFi.localIP().toString().c_str());
  Serial.print("Broadcast message is ");
  Serial.println(broadcastMsg);
}

void setup_lighting(){
  LEDS.addLeds<WS2812,LEDPIN,RGB>(leds,NUMLEDS);
  LEDS.setBrightness(255);
}

void readClock(){
  curTime = millis();
}

void handleFrame(int offset, int dataLength){
  uint8_t brightness;
  int i;
  brightness = (uint8_t)packetBuffer[offset];
  offset += 1;
  if(dataLength < NUMLEDS*3 + 1){ //r,g,b for each led + brightness
    Serial.println("Received an invalid length");
    return;
  }
  for(i=0; i<NUMLEDS; i++){
    leds[i].r = packetBuffer[offset+i*3];
    leds[i].g = packetBuffer[offset+i*3 + 1];
    leds[i].b = packetBuffer[offset+i*3 + 2];
  }
  FastLED.setBrightness(brightness);
  FastLED.show();

} 

void handleMessage(int packetLength){
  unsigned char opcode;
  opcode = packetBuffer[0];

  if(opcode == 0){
    handleFrame(1, packetLength-1);
  }
  else{
    Serial.print("Handling unknown opcode: ");
    Serial.println(opcode);
  }

}

void checkUdpInput(){
  int packetSize;
  int packet_len;
  packetSize = Udp.parsePacket();
  if(packetSize){
    packet_len = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    packetBuffer[packet_len] = 0; // delimit the string
    Serial.println(packet_len);
    handleMessage(packet_len);
    /*Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.write(packetBuffer);
    Udp.endPacket();*/

  }
}

void broadcast(){
  if(bcasttimer < curTime){
    Serial.println("Writing Broadcast");
    Udp.beginPacket(broadcastIP, 2566);
    Udp.write(broadcastMsg);
    Udp.endPacket();
    bcasttimer = curTime+1000*10; //should go every 10 seconds
  }
}

void setup() {
  setup_serial();
  setup_lighting();
  setup_wifi();
  // put your setup code here, to run once:
}

void loop() {
  checkUdpInput();
  readClock();
  // put your main code here, to run repeatedly:
  broadcast();
}