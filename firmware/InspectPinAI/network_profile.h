#pragma once
#include <Arduino.h>
namespace NetworkProfile {
struct Profile { String ssid, password, origin, token; };
const Profile &active();
void load();
void configureUsb();
}
