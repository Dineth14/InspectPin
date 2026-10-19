#include "api_client.h"
#include "config.h"
#include "wav_utils.h"
#include <HTTPClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <SD.h>
namespace {
bool start(HTTPClient &http, WiFiClient &client, const String &route) {
  String base=IP_SERVER_URL;
  // Trusted LAN HTTP only; no silent downgrade or insecure cloud TLS.
  if (!base.startsWith("http://")) return false;
  while (base.endsWith("/")) base.remove(base.length()-1);
  http.setConnectTimeout(Config::httpTimeoutMs); http.setTimeout(Config::httpTimeoutMs);
  http.useHTTP10(true); http.setReuse(false);
  if (!http.begin(client,base+route)) return false;
  http.addHeader("X-Device-Token",IP_DEVICE_TOKEN); return true;
}
bool jsonReply(HTTPClient &http, JsonDocument &doc) {
  int length=http.getSize();
  if (length<=0 || length>8192) return false;
  String body=http.getString();
  return body.length()==size_t(length) && !deserializeJson(doc,body);
}
bool validJob(const String &s) {
  if (s.length()!=32) return false;
  for (char c:s) if (!isxdigit(c)) return false;
  return true;
}
String httpError(int code) { return String("HTTP_")+code; }
}
bool Api::upload(const String &path, String &job, String &error) {
  File f=SD.open(path,FILE_READ);
  if (!f) { error="SD_OPEN_FAILED"; return false; }
  bool image=path.endsWith(".jpg"); uint32_t pcm=0;
  if (!image && !Wav::validate(f,pcm)) { f.close(); error="INVALID_WAV"; return false; }
  f.seek(0);
  WiFiClient client; HTTPClient http;
  if (!start(http,client,String("/api/v1/jobs/")+(image?"image":"voice"))) { f.close(); error="INVALID_SERVER_URL"; return false; }
  http.addHeader("Content-Type",image?"image/jpeg":"audio/wav");
  Serial.printf("HTTP upload started bytes=%lu\n",(unsigned long)f.size());
  int code=http.sendRequest("POST",&f,f.size()); f.close();
  JsonDocument doc; bool ok=code==202 && jsonReply(http,doc);
  if (ok) { job=doc["id"].as<String>(); ok=validJob(job); }
  if (!ok) error=httpError(code);
  http.end(); return ok;
}
bool Api::poll(const String &job, JobResult &result, String &error) {
  if (!validJob(job)) { error="INVALID_JOB_ID"; return false; }
  WiFiClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/jobs/"+job)) { error="INVALID_SERVER_URL"; return false; }
  int code=http.GET(); JsonDocument doc; bool ok=code==200 && jsonReply(http,doc);
  if (ok) {
    result.status=doc["status"].as<String>(); result.transcript=doc["transcript"].as<String>();
    result.answer=doc["answer"].as<String>(); result.audio=doc["audio_available"] | false;
    result.error=doc["error"]["code"].as<String>();
    ok=result.status=="queued" || result.status=="processing" || result.status=="completed" || result.status=="failed";
  }
  if (!ok) error=httpError(code);
  http.end(); return ok;
}
bool Api::download(const String &job, const String &destination, String &error) {
  if (!validJob(job)) { error="INVALID_JOB_ID"; return false; }
  WiFiClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/jobs/"+job+"/audio")) { error="INVALID_SERVER_URL"; return false; }
  const char *keys[]={"Content-Type"}; http.collectHeaders(keys,1);
  int code=http.GET(),length=http.getSize();
  if (code!=200 || length<44 || size_t(length)>Config::maxAnswerBytes || !http.header("Content-Type").startsWith("audio/wav")) {
    error=httpError(code)+"_AUDIO_HEADERS"; http.end(); return false;
  }
  String partial=destination+".part"; File f=SD.open(partial,FILE_WRITE);
  if (!f) { error="SD_WRITE_FAILED"; http.end(); return false; }
  auto *stream=http.getStreamPtr(); uint8_t buffer[1024]; size_t total=0;
  uint32_t began=millis(),lastData=began; bool ok=true;
  while (total<size_t(length) && millis()-began<60000 && millis()-lastData<Config::httpTimeoutMs) {
    int avail=stream->available();
    if (avail>0) {
      size_t want=min(sizeof(buffer),min(size_t(avail),size_t(length)-total));
      int got=stream->read(buffer,want);
      if (got<=0 || f.write(buffer,got)!=size_t(got)) { ok=false; break; }
      total+=got; lastData=millis();
    } else if (!http.connected()) break;
    delay(1);
  }
  f.flush(); f.close(); http.end(); uint32_t bytes=0;
  f=SD.open(partial,FILE_READ); ok=ok && total==size_t(length) && Wav::validate(f,bytes); f.close();
  if (ok) { if (SD.exists(destination)) SD.remove(destination); ok=SD.rename(partial,destination); }
  if (!ok) { SD.remove(partial); error="AUDIO_DOWNLOAD_INCOMPLETE_OR_INVALID"; }
  else Serial.printf("Answer audio downloaded: %lu bytes\n",(unsigned long)total);
  return ok;
}
