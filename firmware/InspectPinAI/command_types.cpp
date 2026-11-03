#include "command_types.h"

DeviceCommand Commands::fromSerial(char value) {
  DeviceCommand c; c.source=CommandSource::SERIAL_CONSOLE; c.requestId=String("serial-")+millis();
  switch (value) {
    case 'v': c.type=CommandType::VOICE_START; break;
    case 'c': c.type=CommandType::PHOTO_CAPTURE; break;
    case 'r': c.type=CommandType::RETRY; break;
    case 'i': c.type=CommandType::CONTEXT_GET; break;
    case 'x': c.type=CommandType::CONTEXT_CLEAR; break;
    case 's': c.type=CommandType::SD_TEST; break;
    case 'w': c.type=CommandType::WIFI_CONNECT; break;
    case 'b': c.type=CommandType::BATTERY_GET; break;
    case 'k': c.type=CommandType::CAMERA_DIAGNOSTIC; break;
    case 'p': c.type=CommandType::TONE_PLAY; break;
    case 'z': c.type=CommandType::SLEEP; break;
    case 'u': c.type=CommandType::VIDEO_START; break;
    case 'o': c.type=CommandType::VIDEO_STOP; break;
    case 'm': c.type=CommandType::MEDIA_LIST; break;
    case 'g': c.type=CommandType::MEDIA_DOWNLOAD; break;
    case '?': c.type=CommandType::STATUS_GET; break;
    default: c.type=CommandType::NONE; break;
  }
  return c;
}

const char *Commands::name(CommandType v) {
  static const char *names[]={"NONE","STATUS_GET","VOICE_START","CANCEL","PHOTO_CAPTURE",
    "VIDEO_START","VIDEO_STOP","LIGHT_SET","VOLUME_SET","HAPTIC_SET","BATTERY_GET",
    "MEDIA_LIST","MEDIA_DELETE","SLEEP","RESTART","SETTINGS_GET","SETTINGS_PATCH",
    "RETRY","CONTEXT_GET","CONTEXT_CLEAR","SD_TEST","WIFI_CONNECT","CAMERA_DIAGNOSTIC","TONE_PLAY","MEDIA_DOWNLOAD"};
  unsigned index=unsigned(v); return index<sizeof(names)/sizeof(names[0])?names[index]:"UNKNOWN";
}
CommandType Commands::fromName(const String &value) {
  for(unsigned i=1;i<=unsigned(CommandType::MEDIA_DOWNLOAD);i++)
    if(value==name(CommandType(i))) return CommandType(i);
  return CommandType::NONE;
}
