param(
    [Parameter(Mandatory=$true)][string]$Version,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Build,
    [Parameter(Mandatory=$true)][string]$Notes,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Device,
    [switch]$PublishOnly
)
$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$python='.\.venv\Scripts\python.exe'
$cli=(Get-Command arduino-cli.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
if(!$cli) { $cli="$env:ProgramFiles\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" }
$receiver="$env:LOCALAPPDATA\InspectPin\ota-receiver"
$offline="$env:LOCALAPPDATA\InspectPin\offline-signing"
foreach($required in $python,$cli,"$offline\release-private.pem","$receiver\release-public.pem","firmware/InspectPinAI/ota_trust.local.h"){
    if(!(Test-Path -LiteralPath $required)){ throw "Required OTA setup file is missing. See docs/OTA_AND_SOUND.md." }
}
& $python scripts/firmware_package.py build-identity --version $Version --build $Build
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$output=".build/ota-$Build"
$flags=@('--fqbn','esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,CDCOnBoot=default,FlashSize=8M,PartitionScheme=default_8MB','--libraries','.tools/arduino-user/libraries','--build-property','compiler.cpp.extra_flags=-DIP_USE_SINGLE_LAYER_CONFIG','--build-path',$output)
& $cli compile --jobs 4 @flags firmware/InspectPinAI
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& $python scripts/firmware_package.py publish --receiver-dir $receiver --key "$offline\release-private.pem" --binary "$output/InspectPinAI.ino.bin" --version $Version --build $Build --notes $Notes
if($LASTEXITCODE -ne 0 -or $PublishOnly){exit $LASTEXITCODE}
& $python scripts/approve_firmware.py --device $Device --version $Version
exit $LASTEXITCODE
