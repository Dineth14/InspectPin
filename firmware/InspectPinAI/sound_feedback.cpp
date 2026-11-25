#include "sound_feedback.h"
#include "audio_player.h"
#include "settings_store.h"
#include <cmath>

namespace {
struct Note { uint16_t hz, ms; };
struct Cue { SoundFeedback::Group group; Note notes[5]; };
using namespace SoundFeedback;
constexpr Cue cues[] = {
  {Connection, {{650,65},{900,65},{1250,80}}},
  {Connection, {{1000,65},{0,25},{1500,80}}},
  {Photo, {{1850,25},{0,25},{1200,45}}},
  {Photo, {{1400,60},{0,25},{1900,85}}},
  {Voice, {{1400,115}}},
  {Voice, {{1100,48},{800,52}}},
  {Voice, {{750,30},{0,40},{750,30}}},
  {AudioNote, {{1600,50},{0,25},{1850,65}}},
  {AudioNote, {{1650,55},{0,25},{1100,70}}},
  {Video, {{800,60},{1150,60},{1500,65}}},
  {Video, {{1500,55},{1150,55},{800,70}}},
  {Warning, {{550,80},{0,30},{720,95}}},
  {Connection, {{1200,55}}},
  {Warning, {{480,65},{0,45},{480,65},{0,45},{390,95}}},
  {Connection, {{650,60},{1000,65},{1500,85}}},
  {Connection, {{1000,65},{1500,65},{2100,90}}},
  {Connection, {{1100,60},{0,25},{1600,80}}},
};
}

bool SoundFeedback::play(Event event) {
  const auto &config=SettingsStore::get().sound;
  const auto &cue=cues[static_cast<uint8_t>(event)];
  if (!config.volume || (event!=Event::Test && (!(config.groups&Master) || !(config.groups&cue.group))))
    return true;
  const float amplitude=4800.0f*config.volume/100.0f;
  uint8_t note=0;
  uint32_t index=0;
  const bool played=playPcm([&](int16_t *out,size_t limit) {
    size_t written=0;
    while (written<limit && note<5 && cue.notes[note].ms) {
      const auto part=cue.notes[note];
      const uint32_t length=part.ms*16U;
      // A 5 ms attack and release avoids driving a sharp edge into the amplifier.
      const float envelope=min(1.0f,min(index,length-1-index)/80.0f);
      out[written++]=part.hz?int16_t(amplitude*envelope*sinf(6.2831853f*part.hz*index/16000.0f)):0;
      if (++index==length) { ++note; index=0; }
    }
    return written;
  });
  Serial.printf("Sound event=%u result=%s\n",unsigned(event),played?"played":"failed");
  return played;
}

void SoundFeedback::beforeRecording(Event event) {
  play(event);
  delay(135);
}
