#pragma once
#include <stdint.h>

namespace SoundFeedback {
enum class Event : uint8_t {
  Boot, ReceiverReady, PhotoCaptured, ImageContextReady, Listen,
  VoiceRecorded, Processing, NoteStart, NoteStop, VideoStart, VideoStop,
  OfflineSaved, UploadComplete, Failed, UpdateStart, UpdateSuccess, Test
};
enum Group : uint8_t {
  Master=1, Connection=2, Photo=4, Voice=8, AudioNote=16, Video=32, Warning=64
};
struct Settings {
  uint8_t groups=127;
  uint8_t volume=65;
};
bool play(Event event);
void beforeRecording(Event event);
}
