#include "api_client.h"
#include "config.h"
#include "network_profile.h"
#include "wav_utils.h"
#include "firmware_version.h"
#include "settings_store.h"
#include "ota_manager.h"
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <SD.h>
#include "battery_monitor.h"
#include "charge_status.h"
namespace {
struct RequestClient { WiFiClient plain; WiFiClientSecure secure; };
bool start(HTTPClient &http, RequestClient &client, const String &route,bool firmwareTls=false) {
  String base=firmwareTls?OtaManager::origin():NetworkProfile::active().origin;
  const bool tls=base.startsWith("https://");
  if (!tls && !base.startsWith("http://")) return false;
  while (base.endsWith("/")) base.remove(base.length()-1);
  http.setConnectTimeout(Config::httpTimeoutMs); http.setTimeout(Config::httpTimeoutMs);
  http.useHTTP10(true); http.setReuse(false);
  if(tls){
    const char *certificate=firmwareTls?OtaManager::ca():IP_SERVER_CA_CERT;
    if(strlen(certificate)<100)return false;
    client.secure.setCACert(certificate);
    if(!http.begin(client.secure,base+route))return false;
  } else if (!http.begin(client.plain,base+route)) return false;
  http.addHeader("X-Device-Token",NetworkProfile::active().token);
  http.addHeader("X-Device-ID",Api::deviceId()); return true;
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
String responseError(HTTPClient &http, int code) {
  JsonDocument doc;
  if (code>0 && jsonReply(http,doc) && doc["error"]["code"].is<const char*>())
    return doc["error"]["code"].as<String>();
  return httpError(code);
}
bool readContext(JsonDocument &doc, SessionContext &context) {
  context.offlineRecording=doc["offline_recording"] | false;
  context.contextId=doc["context_id"] | "";
  context.imageId=doc["active_image_id"] | "";
  double remaining=doc["remaining_seconds"] | 0.0;
  if (!validJob(context.contextId) || (context.imageId.length() && !validJob(context.imageId)) || remaining<0 || remaining>86400) return false;
  context.remainingMs=uint32_t(remaining*1000);
  return true;
}
}
String Api::deviceId() {
  if (strlen(IP_DEVICE_ID)) return String(IP_DEVICE_ID);
  char value[24];
  snprintf(value,sizeof(value),"pin-%012llx",ESP.getEfuseMac());
  return String(value);
}
bool Api::uploadRecording(const String &path, String &error) {
  File file=SD.open(path, FILE_READ);
  if (!file || !file.size() || file.size()>8*1024*1024) {error="INVALID_RECORDING_SIZE";return false;}
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/device/recordings")) {error="INVALID_SERVER_URL";return false;}
  http.addHeader("Content-Type",path.endsWith(".avi")?"video/x-msvideo":"audio/wav");
  http.addHeader("Idempotency-Key",path.substring(path.lastIndexOf('/')+1));
  int code=http.sendRequest("POST",&file,file.size());
  JsonDocument receipt;
  bool ok=code==201 && jsonReply(http,receipt) && validJob(receipt["inspection_id"].as<String>());
  if (!ok) error=code==201?"INVALID_RECEIPT":responseError(http,code);
  http.end();
  return ok;
}
bool Api::uploadImage(const String &path, SessionContext &context, String &error) {
  File f=SD.open(path,FILE_READ);
  if (!f || !f.size() || f.size()>2097152) { f.close(); error="INVALID_IMAGE_FILE"; return false; }
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/images")) { f.close(); error="INVALID_SERVER_URL"; return false; }
  http.addHeader("Content-Type","image/jpeg");
  Serial.printf("JPEG streaming upload: %lu bytes\n",(unsigned long)f.size());
  int code=http.sendRequest("POST",&f,f.size()); f.close();
  JsonDocument doc; bool ok=false;
  if (code==201) ok=jsonReply(http,doc) && readContext(doc,context) && validJob(context.imageId);
  else error=responseError(http,code);
  if (!ok && !error.length()) error="INVALID_IMAGE_RESPONSE";
  http.end(); return ok;
}
bool Api::session(SessionContext &context, String &error, bool clear) {
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/session")) { error="INVALID_SERVER_URL"; return false; }
  int code=clear?http.sendRequest("DELETE"):http.GET();
  JsonDocument doc; bool ok=false;
  if (code==200) ok=jsonReply(http,doc) && readContext(doc,context);
  else error=responseError(http,code);
  if (!ok && !error.length()) error="INVALID_CONTEXT_RESPONSE";
  http.end(); return ok;
}
bool Api::upload(const String &path, String &job, String &error,
                 const String &imageId, const String &contextId, String *returnedContext) {
  File f=SD.open(path,FILE_READ);
  if (!f) { error="SD_OPEN_FAILED"; return false; }
  bool image=path.endsWith(".jpg"); uint32_t pcm=0;
  if (!image && !Wav::validate(f,pcm)) { f.close(); error="INVALID_WAV"; return false; }
  f.seek(0);
  if ((imageId.length() && !validJob(imageId)) || (contextId.length() && !validJob(contextId))) {
    f.close(); error="INVALID_CONTEXT_ID"; return false;
  }
  RequestClient client; HTTPClient http;
  String route=String("/api/v1/jobs/")+(image?"image":"voice");
  if (!image) {
    route+="?";
    if (imageId.length()) route+="image_id="+imageId+"&";
    if (contextId.length()) route+="context_id="+contextId;
  }
  if (!start(http,client,route)) { f.close(); error="INVALID_SERVER_URL"; return false; }
  http.addHeader("Content-Type",image?"image/jpeg":"audio/wav");
  Serial.printf("HTTP upload started bytes=%lu\n",(unsigned long)f.size());
  int code=http.sendRequest("POST",&f,f.size()); f.close();
  JsonDocument doc; bool ok=false;
  if (code==202) {
    ok=jsonReply(http,doc);
    if (ok) {
      job=doc["id"].as<String>(); ok=validJob(job);
      if (returnedContext) *returnedContext=doc["context_id"] | "";
    }
  } else error=responseError(http,code);
  if (!ok && !error.length()) error="INVALID_JOB_RESPONSE";
  http.end(); return ok;
}
bool Api::poll(const String &job, JobResult &result, String &error) {
  if (!validJob(job)) { error="INVALID_JOB_ID"; return false; }
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/jobs/"+job)) { error="INVALID_SERVER_URL"; return false; }
  int code=http.GET(); JsonDocument doc; bool ok=code==200 && jsonReply(http,doc);
  if (ok) {
    result.status=doc["status"].as<String>(); result.transcript=doc["transcript"].as<String>();
    result.answer=doc["answer"].as<String>(); result.audio=doc["audio_available"] | false;
    result.error=doc["error"]["code"].as<String>();
    result.hasCommand=false;
    if(doc["device_command"].is<JsonObject>()) {
      JsonObject command=doc["device_command"].as<JsonObject>();
      result.command.type=Commands::fromName(command["type"].as<String>());
      result.command.source=CommandSource::VOICE;
      result.command.requestId=String("voice-")+job;
      JsonObject parameters=command["parameters"].as<JsonObject>();
      if(result.command.type==CommandType::VOLUME_SET) result.command.intValue=parameters["percent"] | -1;
      result.hasCommand=result.command.type!=CommandType::NONE;
    }
    ok=result.status=="queued" || result.status=="processing" || result.status=="completed" || result.status=="failed";
  }
  if (!ok) error=code==200?"INVALID_JOB_RESPONSE":responseError(http,code);
  http.end(); return ok;
}
bool Api::download(const String &job, const String &destination, String &error) {
  if (!validJob(job)) { error="INVALID_JOB_ID"; return false; }
  RequestClient client; HTTPClient http;
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
    feedLoopWDT();
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
bool Api::heartbeat(const String &state, String &error) {
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/device/heartbeat")) { error="INVALID_SERVER_URL"; return false; }
  JsonDocument payload;
  auto battery=Battery::latest(); auto charge=ChargeStatus::latest();
  if(battery.valid){payload["battery_percent"]=battery.percent;payload["battery_voltage"]=battery.volts;}
  else {payload["battery_percent"]=nullptr;payload["battery_voltage"]=nullptr;}
  payload["battery_estimated"]=true;
  const char *chargeName=ChargeStatus::name(charge.state);
  payload["charge_state"]=String(chargeName)=="fault_unsupported"?"fault":chargeName;
  payload["storage_total"]=uint64_t(SD.cardSize());
  payload["storage_free"]=uint64_t(SD.cardSize()-SD.usedBytes());
  payload["sd_present"]=SD.cardType()!=CARD_NONE;
  payload["wifi_rssi"]=WiFi.RSSI(); payload["connection"]="wifi";
  payload["state"]=state;
  FirmwareVersion::write(payload["reported_firmware"].to<JsonObject>());
  const auto &settings=SettingsStore::get();
  payload["sound_settings"]["groups"]=settings.sound.groups;
  payload["sound_settings"]["volume"]=settings.sound.volume;
  payload["sound_settings"]["speech_volume"]=settings.volumePercent;
  String body; serializeJson(payload,body); http.addHeader("Content-Type","application/json");
  int code=http.POST(body); JsonDocument reply;
  bool ok=code==200&&jsonReply(http,reply)&&(reply["accepted"]|false);
  if(!ok)error=responseError(http,code); http.end(); return ok;
}
bool Api::pollRemoteCommand(DeviceCommand &command, String &remoteId, bool &available, String &error) {
  available=false; remoteId=""; command=DeviceCommand{};
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/device/commands")) { error="INVALID_SERVER_URL"; return false; }
  int code=http.GET(); JsonDocument doc; bool ok=code==200&&jsonReply(http,doc);
  if(!ok){error=responseError(http,code);http.end();return false;}
  JsonArray items=doc["items"].as<JsonArray>();
  if(items.size()==0){http.end();return true;}
  JsonObject item=items[0].as<JsonObject>(); JsonObject payload=item["payload"].as<JsonObject>();
  remoteId=item["id"].as<String>(); String type=item["command_type"].as<String>();
  if(!validJob(remoteId)){error="INVALID_REMOTE_COMMAND_ID";http.end();return false;}
  command.source=CommandSource::HTTP;command.requestId=String("remote-")+remoteId;
  if(type=="capture_photo")command.type=CommandType::PHOTO_CAPTURE;
  else if(type=="retry_upload")command.type=CommandType::RETRY;
  else if(type=="status")command.type=CommandType::STATUS_GET;
  else if(type=="set_volume") {command.type=CommandType::VOLUME_SET;command.intValue=payload["percent"]|-1;}
  else if(type=="set_idle_timeout") {command.type=CommandType::SETTINGS_PATCH;command.intValue=(payload["seconds"]|0)*1000;}
  else if(type=="set_sound") {
    command.type=CommandType::SOUND_SET;
    const int groups=payload["groups"]|-1, volume=payload["volume"]|-1;
    command.intValue=groups>=0 && groups<=127 && volume>=0 && volume<=100
        ? (volume<<8)|groups : -1;
  }
  else if(type=="test_sound")command.type=CommandType::SOUND_TEST;
  else {error="UNSUPPORTED_REMOTE_COMMAND";http.end();return false;}
  available=true;http.end();return true;
}
bool Api::acknowledgeRemoteCommand(const String &remoteId, const String &status,
                                   const String &actualState, const String &errorCode) {
  if(!validJob(remoteId))return false;
  RequestClient client; HTTPClient http;
  if(!start(http,client,"/api/v1/device/commands/"+remoteId+"/ack"))return false;
  JsonDocument payload;payload["status"]=status;payload["result"]["actual_state"]=actualState;
  if (status=="completed") {
    const auto &settings=SettingsStore::get();
    payload["result"]["sound_settings"]["groups"]=settings.sound.groups;
    payload["result"]["sound_settings"]["volume"]=settings.sound.volume;
    payload["result"]["sound_settings"]["speech_volume"]=settings.volumePercent;
  }
  if(errorCode.length())payload["result"]["error"]=errorCode;
  String body;serializeJson(payload,body);http.addHeader("Content-Type","application/json");
  int code=http.POST(body);http.end();return code==200;
}

bool Api::firmwareRequest(const String &route,const JsonDocument &payload,JsonDocument &reply) {
  if (!OtaManager::enabled()) return false;
  RequestClient client; HTTPClient http;
  if (!start(http,client,route,true)) return false;
  http.addHeader("Content-Type","application/json");
  String body; serializeJson(payload,body);
  const bool ok=http.POST(body)==200 && jsonReply(http,reply);
  http.end();
  return ok;
}

bool Api::streamFirmware(const String &id,size_t size,
                         const std::function<bool(const uint8_t *,size_t)> &consume) {
  if (!validJob(id) || !OtaManager::enabled()) return false;
  RequestClient client; HTTPClient http;
  if (!start(http,client,"/api/v1/device/firmware/"+id+"/image",true)) return false;
  if (http.GET()!=200 || size_t(http.getSize())!=size) { http.end(); return false; }
  auto *stream=http.getStreamPtr();
  uint8_t chunk[2048];
  size_t total=0;
  const uint32_t started=millis();
  uint32_t last=started;
  while (total<size && http.connected() && millis()-started<120000 && millis()-last<10000) {
    feedLoopWDT();
    const int available=stream->available();
    if (available<=0 || (total==0 && available<24)) { delay(3); continue; }
    const size_t want=min(sizeof(chunk),min(size-total,size_t(available)));
    const int got=stream->read(chunk,want);
    if (got<=0 || !consume(chunk,size_t(got))) break;
    total+=got;
    last=millis();
    delay(1);
  }
  http.end();
  return total==size;
}
