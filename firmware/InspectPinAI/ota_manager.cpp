#include "ota_manager.h"
#include "api_client.h"
#include "audio_player.h"
#include "camera_manager.h"
#include "config.h"
#include "firmware_version.h"
#include "network_profile.h"
#include "sd_manager.h"
#include "sound_feedback.h"
#include <ESP_I2S.h>
#include <Preferences.h>
#include <WiFi.h>
#include <esp_ota_ops.h>
#include <esp_random.h>
#include <mbedtls/base64.h>
#include <mbedtls/pk.h>
#include <mbedtls/sha256.h>
#include <time.h>

#if __has_include("ota_trust.local.h")
#include "ota_trust.local.h"
#define IP_OTA_PROVISIONED 1
#else
constexpr char otaReleasePublicKey[]="";
constexpr char otaGrantPublicKey[]="";
#define IP_OTA_PROVISIONED 0
#endif
#if __has_include("ota_transport.local.h")
#include "ota_transport.local.h"
#else
constexpr char otaReceiverOrigin[]="";
constexpr char otaReceiverCa[]="";
#endif

namespace {
constexpr size_t slotBytes=0x330000;
String result="none";
bool bootValidated=false;
uint32_t lastCheck=0;
Preferences journal;

String hexString(const uint8_t *data,size_t size) {
  constexpr char hex[]="0123456789abcdef";
  String result;
  result.reserve(size*2);
  for (size_t i=0;i<size;++i) {
    result+=hex[data[i]>>4];
    result+=hex[data[i]&15];
  }
  return result;
}

bool isHex(const String &value,size_t length) {
  if (value.length()!=length) return false;
  for (char c:value) if (!((c>='0' && c<='9') || (c>='a' && c<='f'))) return false;
  return true;
}

bool isBuild(const String &value) {
  if (!value.length() || value.length()>48) return false;
  for (char c:value) if (!isalnum(static_cast<unsigned char>(c)) && c!='-' && c!='_' && c!='.') return false;
  return true;
}

uint32_t releaseNumber(const String &input) {
  uint32_t release=0;
  size_t i=0;
  for (unsigned part=0;part<3;++part) {
    unsigned digits=0,value=0;
    const size_t start=i;
    while (i<input.length() && input[i]>='0' && input[i]<='9') {
      if (++digits>3) return 0;
      value=value*10+unsigned(input[i++]-'0');
    }
    if (!digits || (digits>1 && input[start]=='0')) return 0;
    release=release*1000+value;
    if (part<2 && (i>=input.length() || input[i++]!='.')) return 0;
  }
  return i==input.length()?release:0;
}

bool verifies(const char *pem,const String &message,const String &signature) {
  uint8_t hash[32], der[80];
  size_t size=0;
  if (signature.length()>112 ||
      mbedtls_base64_decode(der,sizeof(der),&size,
                           reinterpret_cast<const uint8_t *>(signature.c_str()),signature.length())!=0 ||
      mbedtls_sha256(reinterpret_cast<const uint8_t *>(message.c_str()),message.length(),hash,0)!=0)
    return false;
  mbedtls_pk_context key;
  mbedtls_pk_init(&key);
  const bool ok=mbedtls_pk_parse_public_key(&key,reinterpret_cast<const uint8_t *>(pem),strlen(pem)+1)==0 &&
                mbedtls_pk_can_do(&key,MBEDTLS_PK_ECDSA) &&
                mbedtls_pk_verify(&key,MBEDTLS_MD_SHA256,hash,sizeof(hash),der,size)==0;
  mbedtls_pk_free(&key);
  return ok;
}

bool report(const String &id,const char *state,size_t bytes,const char *detail="") {
  JsonDocument message, response;
  message["state"]=state; message["bytes"]=bytes; message["detail"]=detail;
  message["version"]=FirmwareVersion::version(); message["build"]=FirmwareVersion::build();
  feedLoopWDT();
  return Api::firmwareRequest("/api/v1/device/firmware/"+id+"/progress",message,response) &&
      (response["accepted"]|false);
}

bool checkAudio() {
  AudioLease lease;
  if (!lease) return false;
  I2SClass mic;
  mic.setPinsPdmRx(Config::micClock,Config::micData);
  if (!mic.begin(I2S_MODE_PDM_RX,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)) return false;
  mic.end();
  I2SClass speaker;
  speaker.setPins(Config::bclk,Config::ws,Config::dout);
  if (!speaker.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)) return false;
  speaker.end();
  return true;
}

void install(JsonDocument &offer,const String &challenge) {
  using E=SoundFeedback::Event;
  const String id=offer["update"]|String();
  if (!isHex(id,32)) return;
  const JsonObjectConst manifest=offer["manifest"].as<JsonObjectConst>();
  const String version=manifest["version"]|String(), build=manifest["build"]|String();
  const String digest=manifest["sha256"]|String(), hardware=manifest["hardware"]|String();
  const String target=manifest["target"]|String();
  const uint32_t size=manifest["size"]|0UL, requirement=manifest["slot_bytes"]|0UL;
  const auto *next=esp_ota_get_next_update_partition(nullptr);
  const String metadata=String("InspectPin firmware v1\n")+version+"\n"+build+"\n"+target+"\n"+
      hardware+"\n"+size+"\n"+digest+"\n"+requirement+"\n";
  const String grant=String("InspectPin approval v1\n")+Api::deviceId()+"\n"+id+"\n"+challenge+"\n"+digest+"\n";
  if (!next || next==esp_ota_get_running_partition() || requirement!=slotBytes || next->size<requirement ||
      size<256 || size>next->size || !isHex(digest,64) || !isBuild(build) ||
      hardware!=FirmwareVersion::hardware() || target!="esp32s3" ||
      releaseNumber(version)<=FirmwareVersion::releaseNumber() ||
      !verifies(otaReleasePublicKey,metadata,manifest["signature"]|String()) ||
      !verifies(otaGrantPublicKey,grant,offer["grant"]|String())) {
    report(id,"failed",0,"Invalid signature, version or hardware compatibility");
    result="package rejected";
    SoundFeedback::play(E::Failed);
    return;
  }
  result="downloading";
  SoundFeedback::play(E::UpdateStart);
  mbedtls_sha256_context hash;
  mbedtls_sha256_init(&hash);
  mbedtls_sha256_starts(&hash,0);
  size_t received=0, lastReport=0;
  esp_ota_handle_t handle=0;
  bool opened=false;
  bool ok=Api::streamFirmware(id,size,[&](const uint8_t *chunk,size_t count) {
    if (!opened) {
      if (count<14 || chunk[0]!=0xe9 || chunk[12]!=9 || chunk[13]!=0 ||
          esp_ota_begin(next,OTA_WITH_SEQUENTIAL_WRITES,&handle)!=ESP_OK) return false;
      opened=true;
    }
    if (esp_ota_write(handle,chunk,count)!=ESP_OK || mbedtls_sha256_update(&hash,chunk,count)!=0) return false;
    received+=count;
    if (received-lastReport>=256*1024) {
      report(id,"downloading",received);
      lastReport=received;
    }
    return true;
  });
  uint8_t actual[32];
  ok=ok && opened && mbedtls_sha256_finish(&hash,actual)==0 && hexString(actual,sizeof(actual))==digest;
  mbedtls_sha256_free(&hash);
  if (ok) {
    report(id,"verifying",received);
    ok=esp_ota_end(handle)==ESP_OK;
    opened=false;
  }
  if (opened) esp_ota_abort(handle);
  if (ok) {
    JsonDocument record;
    record["id"]=id; record["version"]=version; record["build"]=build; record["size"]=size;
    String saved; serializeJson(record,saved);
    const bool journalReady=journal.begin("ip-ota",false);
    ok=journalReady && journal.putString("pending",saved)==saved.length();
    if (journalReady) journal.end();
    if (ok) ok=report(id,"installing",received) && report(id,"restarting",received);
    if (ok) ok=esp_ota_set_boot_partition(next)==ESP_OK;
    if (ok) { Serial.println("OTA verified; restarting into inactive slot"); delay(50); ESP.restart(); }
    if (journal.begin("ip-ota",false)) { journal.remove("pending"); journal.end(); }
  }
  result="update failed";
  report(id,"failed",received,"Transfer, verification or boot selection failed");
  SoundFeedback::play(E::Failed);
}
}

bool OtaManager::enabled() {
  return IP_OTA_PROVISIONED && origin().startsWith("https://") && strlen(ca())>=100;
}
String OtaManager::origin() {
  const String configured=NetworkProfile::active().origin;
  if (configured.startsWith("https://")) return configured;
  if (!configured.startsWith("http://") || !otaReceiverOrigin[0]) return String();
  auto host=[](const String &url,int offset) {
    const int colon=url.indexOf(':',offset);
    return colon<0?url.substring(offset):url.substring(offset,colon);
  };
  return host(configured,7)==host(otaReceiverOrigin,8)?String(otaReceiverOrigin):String();
}
const char *OtaManager::ca() {
  return NetworkProfile::active().origin.startsWith("https://")?IP_SERVER_CA_CERT:otaReceiverCa;
}
const char *OtaManager::lastResult() { return result.c_str(); }

void OtaManager::verifyBoot(bool settingsReady,bool storageReady) {
  if (journal.begin("ip-ota",true)) {
    result=journal.getString("last","none");
    journal.end();
  }
  const auto *running=esp_ota_get_running_partition();
  esp_ota_img_states_t state;
  if (!running || esp_ota_get_state_partition(running,&state)!=ESP_OK) return;
  bootValidated=state==ESP_OTA_IMG_VALID;
  if (state!=ESP_OTA_IMG_PENDING_VERIFY) return;
  const auto &network=NetworkProfile::active();
  if (!settingsReady || !storageReady || !network.ssid.length() || !network.token.length() ||
      !enabled() || !Store::selfTest() || !diagnoseCamera() || !checkAudio()) {
    result="boot validation failed";
    Serial.println("OTA boot validation failed; requesting automatic rollback");
    esp_ota_mark_app_invalid_rollback_and_reboot();
    return;
  }
  if (esp_ota_mark_app_valid_cancel_rollback()==ESP_OK) {
    bootValidated=true;
    result="local boot validated";
    Serial.println("OTA boot validation passed");
  }
}

void OtaManager::service() {
  if (!enabled() || WiFi.status()!=WL_CONNECTED || millis()-lastCheck<15000) return;
  lastCheck=millis();
  if (time(nullptr)<1735689600) { // Wait for a real clock before certificate validation.
    configTime(0,0,"pool.ntp.org","time.google.com");
    return;
  }
  if (journal.begin("ip-ota",false)) {
    JsonDocument record;
    const String pending=journal.getString("pending","");
    if (pending.length() && !deserializeJson(record,pending)) {
      const String id=record["id"]|String();
      const bool expected=bootValidated && String(FirmwareVersion::version())==(record["version"]|String()) &&
                          String(FirmwareVersion::build())==(record["build"]|String());
      if (isHex(id,32) && report(id,expected?"confirmed":"failed",record["size"]|0UL,
                               expected?"Application restarted and validated":"Rolled back or boot did not match")) {
        journal.remove("pending");
        result=expected?"confirmed":"rolled back";
        journal.putString("last",result);
        SoundFeedback::play(expected?SoundFeedback::Event::UpdateSuccess:SoundFeedback::Event::Failed);
      }
      journal.end();
      return;
    }
    journal.end();
  }
  uint8_t random[16];
  esp_fill_random(random,sizeof(random));
  const String challenge=hexString(random,sizeof(random));
  JsonDocument payload, offer;
  payload["challenge"]=challenge;
  if (Api::firmwareRequest("/api/v1/device/firmware/offer",payload,offer) &&
      offer["update"].is<const char *>()) install(offer,challenge);
}
