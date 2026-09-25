// Standalone LAN display. No OpenAI credentials or inference on this device.
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <Preferences.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <ArduinoJson.h>
#include "board_config.h"
#include "setup_page.h"
#include "smooth_fonts.h"

#ifndef CODEX_DEMO
#define CODEX_DEMO 0
#endif

Adafruit_ILI9341 lcd(&SPI, LCD_DC, LCD_CS, LCD_RST);
GFXcanvas16 canvas(240,320);
WebServer portal(80);
Preferences preferences;
JsonDocument snapshot;
String ssid, password, serverBase, setupSsid, setupPassword;
bool provisioning=false, saved=false, haveData=false, fetchFailed=false, touched=false;
uint8_t page=0, detailOffset=0;
uint32_t receivedAt=0, lastFetch=0, lastDraw=0, lastReconnect=0, bootHeld=0;
int touchStartX=0, touchStartY=0, touchLastY=0;
const uint16_t BG=0x0000, FG=0xFFFF, MUTED=0xFFFF, ACCENT=0xFFFF, LINE=0x4208, WARNING=0xFFFF;

const SmoothFont &fontFor(int size){return smoothFonts[size>=6?4:size>=4?3:size>=3?2:size>=2?1:0];}
int textWidth(const String &s,int size=1){
  const SmoothFont &font=fontFor(size);int width=0;
  for(size_t i=0;i<s.length();i++){uint8_t c=s[i];if(c<32||c>126)c='?';width+=font.glyphs[c-32].advance;}
  return width;
}
void label(int x,int y,const String &s,int size=1,uint16_t color=FG){
  const SmoothFont &font=fontFor(size);
  uint16_t colors[16];
  for(int a=0;a<16;a++){
    int r=(((color>>11)&31)*a+((BG>>11)&31)*(15-a)+7)/15;
    int g=(((color>>5)&63)*a+((BG>>5)&63)*(15-a)+7)/15;
    int b=((color&31)*a+(BG&31)*(15-a)+7)/15;
    colors[a]=(r<<11)|(g<<5)|b;
  }
  for(size_t i=0;i<s.length();i++){
    uint8_t c=s[i];if(c<32||c>126)c='?';const SmoothGlyph &glyph=font.glyphs[c-32];
    for(int py=0;py<glyph.h;py++)for(int px=0;px<glyph.w;px++){
      int n=py*glyph.w+px;uint8_t packed=pgm_read_byte(font.pixels+glyph.offset+n/2);
      uint8_t a=n%2?packed&15:packed>>4;
      if(a)canvas.drawPixel(x+glyph.x+px,y+glyph.y+py,colors[a]);
    }
    x+=glyph.advance;
  }
}
void right(int y,const String &s,int size=1,uint16_t color=FG){label(228-textWidth(s,size),y,s,size,color);}
void center(int y,const String &s,int size=1,uint16_t color=FG){label((240-textWidth(s,size))/2,y,s,size,color);}
String compact(double n){
  if(n<0)return "--";
  const char *units[]={"","K","M","B","T"};int i=0;
  while(n>=1000&&i<4){n/=1000;i++;}
  return String(n,i?2:0)+units[i];
}
double numberOrMissing(JsonVariantConst v){return v.isNull()?-1:v.as<double>();}
String elapsedText(double seconds){
  if(seconds<0)return "Collecting";
  uint64_t value=(uint64_t)seconds;
  if(value>=86400)return String((unsigned long)(value/86400))+"d "+String((unsigned long)(value%86400/3600))+"h";
  if(value>=3600)return String((unsigned long)(value/3600))+"h "+String((unsigned long)(value%3600/60))+"m";
  return String((unsigned long)(value/60))+"m";
}
void row(int y,const String &name,const String &value,uint16_t color=FG){label(12,y,name,1,MUTED);right(y,value,1,color);}
void draw(){
  canvas.fillScreen(BG);
  if(provisioning){
    label(12,20,"CONNECT YOUR DISPLAY",1,ACCENT);
    label(12,58,"Join this Wi-Fi:");label(12,78,setupSsid,1,ACCENT);
    label(12,112,"Setup password:");label(12,132,setupPassword,2,ACCENT);
    label(12,178,"Open in your browser:");label(12,200,"http://192.168.4.1");
    label(12,249,"Choose your 2.4 GHz Wi-Fi");label(12,268,"and dashboard address.");
    lcd.drawRGBBitmap(0,0,canvas.getBuffer(),240,320);return;
  }
  double serverNow=haveData?snapshot["server_time"].as<double>()+(uint32_t)(millis()-receivedAt)/1000.0:0;
  double updated=numberOrMissing(snapshot["updated_at"]);
  double reset=numberOrMissing(snapshot["weekly"]["resets_at"]);
  bool offline=!CODEX_DEMO&&(WiFi.status()!=WL_CONNECTED||fetchFailed);
  double freshness=snapshot["stale_seconds"]|900;
  bool stale=!haveData||String(snapshot["state"]|"")!="fresh"||serverNow-updated>freshness||(reset>=0&&serverNow>=reset);
  bool tokenFresh=haveData&&(snapshot["tokens_fresh"]|false)&&serverNow-numberOrMissing(snapshot["tokens_updated_at"])<=freshness;
  label(12,15,page?"Total Tokens used -":"WEEKLY CODEX",1,ACCENT);right(15,page?"02/02":"01/02",1,MUTED);
  if(!page){
    double remaining=numberOrMissing(snapshot["weekly"]["remaining_percent"]);
    String value=remaining<0?"--":String(remaining,0);
    if(remaining==0){
      label(16,56,"0",4,FG);label(42,72,"%",2,ACCENT);
      double balance=numberOrMissing(snapshot["credits"]["balance"]);
      String creditValue=stale||offline?"--":(snapshot["credits"]["unlimited"]|false)?"Unlimited":balance<0?"--":compact(floor(balance));
      right(70,"(Credits Left: "+creditValue+")",1,ACCENT);
    }else{
      int width=textWidth(value,6)+5+textWidth("%",3);int x=(240-width)/2;
      label(x,45,value,6,FG);label(x+textWidth(value,6)+5,65,"%",3,ACCENT);
    }
    center(104,"REMAINING",1,MUTED);
    canvas.fillRoundRect(12,127,216,9,4,LINE);
    if(remaining>0)canvas.fillRoundRect(12,127,(int)(216*remaining/100),9,4,ACCENT);
    double points=numberOrMissing(snapshot["today"]["points"]);
    row(160,"Weekly Used Today",points<0?"--":String(points,1)+"%");
    row(188,"Tokens today*",tokenFresh?compact(numberOrMissing(snapshot["today"]["tokens"])):"--");
    row(216,"Est. runway",stale||offline?"Unavailable":elapsedText(numberOrMissing(snapshot["runway"]["seconds"])),ACCENT);
    String resetLabel=snapshot["weekly"]["reset_local_label"]|"";
    String resetTitle=resetLabel.isEmpty()?"Resets in":"Resets in ("+resetLabel+")";
    row(244,resetTitle,reset<0?"--":elapsedText(max(0.0,reset-serverNow)));
  }else{
    label(12,32,snapshot["weekly"]["period_date_label"]|"--/-- to --/--",1,MUTED);
    String total=compact(numberOrMissing(snapshot["period"]["tokens"]));
    center(51,total,3);center(79,"OBSERVED TOKENS*",1,MUTED);
    double average=numberOrMissing(snapshot["period"]["average_points_per_day"]);
    row(101,"Average pace",average<0?"--":String(average,1)+" pts/d");
    canvas.drawFastHLine(12,119,216,LINE);
    label(12,130,"DAY",1,MUTED);label(93,130,"PTS*",1,MUTED);right(130,"TOKENS*",1,MUTED);
    JsonArrayConst days=snapshot["days"].as<JsonArrayConst>();
    for(int i=0;i<4&&i+detailOffset<(int)days.size();i++){
      JsonObjectConst day=days[i+detailOffset];int y=151+i*23;
      String date=day["date"]|"";label(12,y,date.substring(5));
      double points=numberOrMissing(day["points"]);label(93,y,points<0?"--":String(points,1));
      right(y,compact(numberOrMissing(day["tokens"])));
    }
    label(12,258,"LIFETIME TOKENS",1,MUTED);
    right(253,tokenFresh?compact(numberOrMissing(snapshot["lifetime_tokens"])):"--",2,ACCENT);
    label(12,278,"* observed / partial",1,MUTED);
  }
  canvas.drawFastHLine(12,294,216,LINE);
  String status=CODEX_DEMO?"DEMO":offline?"SERVER OFFLINE":stale?"DATA STALE":"Updated "+elapsedText(serverNow-updated)+" ago";
  label(12,302,status,1,(offline||stale)?WARNING:MUTED);
  lcd.drawRGBBitmap(0,0,canvas.getBuffer(),240,320);
}

bool validServer(const String &value){
  // Intentionally a private IPv4 LAN HTTP endpoint, not arbitrary internet URLs.
  if(!value.startsWith("http://")||value.length()>64)return false;
  String host=value.substring(7);int colon=host.indexOf(':');
  String port=colon<0?"80":host.substring(colon+1);host=colon<0?host:host.substring(0,colon);
  for(size_t i=0;i<port.length();i++)if(!isDigit(port[i]))return false;
  if(port.toInt()<1||port.toInt()>65535)return false;
  IPAddress ip;if(!ip.fromString(host))return false;
  return ip[0]==10||(ip[0]==192&&ip[1]==168)||(ip[0]==172&&ip[1]>=16&&ip[1]<=31);
}
String serialSetupLine;
void serialSetup(){
  // Physical USB setup convenience; accepts only a non-secret dashboard URL.
  while(Serial.available()){
    char c=Serial.read();
    if(c=='\n'){
      serialSetupLine.trim();
      if(serialSetupLine.startsWith("server ")){
        String value=serialSetupLine.substring(7);value.trim();
        while(value.endsWith("/"))value.remove(value.length()-1);
        if(validServer(value)&&preferences.putString("server",value)>0&&preferences.getString("server","")==value)
          Serial.println("Dashboard default saved");
        else Serial.println("Dashboard default rejected or storage unavailable");
      }
      serialSetupLine="";
    }else if(serialSetupLine.length()<100)serialSetupLine+=c;
    else serialSetupLine="";
  }
}
void startPortal(){
  provisioning=true;WiFi.disconnect();WiFi.mode(WIFI_AP_STA);
  setupSsid="Codex-Setup-"+String((uint32_t)ESP.getEfuseMac(),HEX).substring(0,4);
  char pass[9];snprintf(pass,sizeof(pass),"%08lX",(unsigned long)esp_random());setupPassword=pass;
  WiFi.softAP(setupSsid.c_str(),setupPassword.c_str(),1,false,1);
  portal.on("/",HTTP_GET,[]{portal.sendHeader("Cache-Control","no-store");portal.send_P(200,"text/html; charset=utf-8",SETUP_PAGE);});
  portal.on("/settings",HTTP_GET,[]{
    JsonDocument data;data["server"]=preferences.getString("server","");data["ssid"]=preferences.getString("ssid","");
    String body;serializeJson(data,body);portal.sendHeader("Cache-Control","no-store");portal.send(200,"application/json",body);
  });
  portal.on("/networks",HTTP_GET,[]{
    int count=WiFi.scanComplete();JsonDocument data;
    if(count==WIFI_SCAN_FAILED){WiFi.scanNetworks(true,false,false,120);data["scanning"]=true;}
    else if(count==WIFI_SCAN_RUNNING){data["scanning"]=true;}
    else{
      data["scanning"]=false;JsonArray networks=data["networks"].to<JsonArray>();
      for(int i=0;i<count&&i<40;i++){
        if(WiFi.SSID(i).isEmpty())continue;
        JsonObject network=networks.add<JsonObject>();network["ssid"]=WiFi.SSID(i);network["rssi"]=WiFi.RSSI(i);network["open"]=WiFi.encryptionType(i)==WIFI_AUTH_OPEN;
      }
      WiFi.scanDelete();
    }
    String body;serializeJson(data,body);portal.sendHeader("Cache-Control","no-store");portal.send(200,"application/json",body);
  });
  portal.on("/save",HTTP_POST,[]{
    String s=portal.arg("ssid"),p=portal.arg("password"),base=portal.arg("server");base.trim();
    while(base.endsWith("/"))base.remove(base.length()-1);
    if(s.length()<1||s.length()>32){portal.send(400,"text/plain","Choose a Wi-Fi network or enter its name (up to 32 bytes).");return;}
    if(p.length()<8||p.length()>63){portal.send(400,"text/plain","Enter a Wi-Fi password between 8 and 63 characters.");return;}
    if(!validServer(base)){portal.send(400,"text/plain","Enter your collector's private LAN address, such as http://192.168.1.100:8790.");return;}
    bool stored=preferences.putString("ssid",s)>0;
    stored=(preferences.putString("password",p)>0)&&stored;
    stored=(preferences.putString("server",base)>0)&&stored;
    stored=stored&&preferences.getString("ssid","")==s&&preferences.getString("password","")==p&&preferences.getString("server","")==base;
    if(!stored){portal.send(500,"text/plain","Settings could not be stored. Stay connected and retry, or reset the display.");return;}
    portal.send(200,"text/plain","Saved. The display will restart and connect. Rejoin your normal Wi-Fi.");saved=true;
  });
  portal.onNotFound([]{portal.send(404,"text/plain","Not found");});portal.begin();draw();
}
void fetch(){
  lastFetch=millis();if(WiFi.status()!=WL_CONNECTED){fetchFailed=true;return;}
  WiFiClient client;HTTPClient http;
  if(!http.begin(client,serverBase+"/api/display")){fetchFailed=true;return;}
  http.setConnectTimeout(3000);http.setTimeout(3000);
  int code=http.GET();int size=http.getSize();
  if(code==200&&size>0&&size<=16384){
    JsonDocument next;String body=http.getString();
    DeserializationError err=deserializeJson(next,body);
    if(!err&&next["schema_version"]==1&&next["server_time"].is<double>()&&next["days"].is<JsonArray>()){
      snapshot=next;receivedAt=millis();haveData=true;fetchFailed=false;
    }else fetchFailed=true;
  }else fetchFailed=true;
  http.end();
}
bool readTouch(int &x,int &y){
  Wire.beginTransmission(TOUCH_ADDR);Wire.write((uint8_t)0x02);
  if(Wire.endTransmission(false)!=0)return false;
  if(Wire.requestFrom(TOUCH_ADDR,(uint8_t)5)!=(uint8_t)5)return false;
  uint8_t count=Wire.read()&0x0F,xh=Wire.read(),xl=Wire.read(),yh=Wire.read(),yl=Wire.read();
  if(count<1||count>2)return false;
  x=((xh&0x0F)<<8)|xl;y=((yh&0x0F)<<8)|yl;
  if(TOUCH_SWAP_XY){int tmp=x;x=y;y=tmp;}
  if(TOUCH_INVERT_X)x=239-x;if(TOUCH_INVERT_Y)y=319-y;
  if(DISPLAY_ROTATION==2){x=239-x;y=319-y;}
  return x>=0&&x<240&&y>=0&&y<320;
}
void setup(){
  Serial.begin(115200);
  pinMode(LCD_BL,OUTPUT);digitalWrite(LCD_BL,LOW);pinMode(BOOT_BUTTON,INPUT_PULLUP);
  SPI.begin(LCD_SCK,LCD_MISO,LCD_MOSI,LCD_CS);lcd.begin(DISPLAY_SPI_HZ);
  lcd.invertDisplay(DISPLAY_INVERT);lcd.setRotation(DISPLAY_ROTATION);digitalWrite(LCD_BL,HIGH);
  Wire.begin(TOUCH_SDA,TOUCH_SCL);Wire.setTimeOut(20);
  pinMode(TOUCH_INT,INPUT);pinMode(TOUCH_RST,OUTPUT);digitalWrite(TOUCH_RST,LOW);delay(20);digitalWrite(TOUCH_RST,HIGH);delay(150);
  preferences.begin("codexdesk",false);
  if(CODEX_DEMO){
    deserializeJson(snapshot,R"({"schema_version":1,"server_time":1000000,"updated_at":1000000,"state":"fresh","weekly":{"remaining_percent":33,"resets_at":1262800},"today":{"points":8.2,"tokens":142600000},"runway":{"seconds":176400},"period":{"tokens":921000000,"average_points_per_day":8.1},"lifetime_tokens":1234567890,"tokens_updated_at":1000000,"tokens_fresh":true,"days":[{"date":"2026-09-22","points":8.2,"tokens":142600000}]})");
    receivedAt=millis();haveData=true;draw();return;
  }
  ssid=preferences.getString("ssid","");password=preferences.getString("password","");serverBase=preferences.getString("server","");
  if(ssid.isEmpty()||!validServer(serverBase)){startPortal();return;}
  WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(true);WiFi.begin(ssid.c_str(),password.c_str());draw();
}
void loop(){
  uint32_t now=millis();
  if(!digitalRead(BOOT_BUTTON)){
    if(!bootHeld)bootHeld=now;
    if(now-bootHeld>5000){preferences.clear();ESP.restart();}
  }else bootHeld=0;
  if(provisioning){serialSetup();portal.handleClient();if(saved){delay(500);ESP.restart();}delay(5);return;}
  if(!CODEX_DEMO){
    if(WiFi.status()!=WL_CONNECTED&&now-lastReconnect>=30000){lastReconnect=now;WiFi.reconnect();}
    if((!lastFetch&&WiFi.status()==WL_CONNECTED)||now-lastFetch>=30000)fetch();
  }
  int x,y;
  if(readTouch(x,y)){
    if(!touched){touchStartX=x;touchStartY=y;}touchLastY=y;touched=true;
  }else if(touched){
    if(page&&abs(touchLastY-touchStartY)>40){detailOffset=touchLastY<touchStartY?4:0;}
    else{page=1-page;detailOffset=0;}
    touched=false;draw();
  }
  if(now-lastDraw>=1000){lastDraw=now;draw();}
  delay(10);
}
