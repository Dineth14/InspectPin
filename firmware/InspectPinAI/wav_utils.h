#pragma once
#include <FS.h>
namespace Wav {
bool writeHeader(File &file, uint32_t bytes);
bool validate(File &file, uint32_t &pcmBytes);
}
