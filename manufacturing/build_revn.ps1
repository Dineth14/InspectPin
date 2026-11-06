param(
  [string]$ArduinoCli = "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe",
  [string]$Output = "$PSScriptRoot\output"
)
$ErrorActionPreference = "Stop"
$fqbn = "esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=8M,PartitionScheme=default_8MB"
$expectedCore = "3.3.12"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$core = & $ArduinoCli core list | Select-String '^esp32:esp32\s+' | ForEach-Object { ($_ -split '\s+')[1] }
if ($core -ne $expectedCore) { throw "Expected esp32:esp32 $expectedCore, found '$core'." }
$appBuild = Join-Path $root ".build\revn-application"
$factoryBuild = Join-Path $root ".build\revn-factory"
& $ArduinoCli compile --fqbn $fqbn --build-property "compiler.cpp.extra_flags=-DIP_USE_REV_N_CONFIG" --output-dir $appBuild "$root\firmware\InspectPinAI"
if ($LASTEXITCODE) { throw "Application compile failed." }
& $ArduinoCli compile --fqbn $fqbn --output-dir $factoryBuild "$root\firmware\InspectPinFactoryTest"
if ($LASTEXITCODE) { throw "Factory compile failed." }
New-Item -ItemType Directory -Force $Output, "$Output\application_components", "$Output\factory_components" | Out-Null
Copy-Item "$appBuild\InspectPinAI.ino.merged.bin" "$Output\inspectpin_revn_application.bin" -Force
Copy-Item "$factoryBuild\InspectPinFactoryTest.ino.merged.bin" "$Output\inspectpin_revn_factory.bin" -Force
Copy-Item "$appBuild\InspectPinAI.ino.bootloader.bin" "$Output\application_components\bootloader.bin" -Force
Copy-Item "$appBuild\InspectPinAI.ino.partitions.bin" "$Output\application_components\partitions.bin" -Force
Copy-Item "$appBuild\boot_app0.bin" "$Output\application_components\boot_app0.bin" -Force
Copy-Item "$appBuild\InspectPinAI.ino.bin" "$Output\application_components\application.bin" -Force
Copy-Item "$factoryBuild\InspectPinFactoryTest.ino.bootloader.bin" "$Output\factory_components\bootloader.bin" -Force
Copy-Item "$factoryBuild\InspectPinFactoryTest.ino.partitions.bin" "$Output\factory_components\partitions.bin" -Force
Copy-Item "$factoryBuild\boot_app0.bin" "$Output\factory_components\boot_app0.bin" -Force
Copy-Item "$factoryBuild\InspectPinFactoryTest.ino.bin" "$Output\factory_components\application.bin" -Force
Get-ChildItem $Output -Recurse -File -Filter *.bin | Get-FileHash -Algorithm SHA256 | ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), $_.Path.Substring($Output.Length + 1).Replace('\','/') } | Set-Content "$Output\SHA256SUMS.txt"
Write-Host "Rev N application and factory images compiled and staged in $Output"
