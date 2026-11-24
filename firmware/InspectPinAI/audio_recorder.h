#pragma once
#include <Arduino.h>
#include "button_manager.h"
bool recordWav(const String &path, ButtonManager *noteControls=nullptr);
