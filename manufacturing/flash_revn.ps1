param(
  [Parameter(Mandatory=$true)][string]$Port,
  [ValidateSet("application","factory")][string]$Target = "factory",
  [string]$Esptool = "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
)
$ErrorActionPreference = "Stop"
$image = Join-Path "$PSScriptRoot\output" "inspectpin_revn_$Target.bin"
if (!(Test-Path $image)) { throw "Missing $image. Run build_revn.ps1 first." }
if (!(Test-Path $Esptool)) { throw "esptool not found at $Esptool" }
& $Esptool --chip esp32s3 --port $Port --baud 921600 write-flash --flash-mode dio --flash-freq 80m --flash-size 8MB 0x0 $image
if ($LASTEXITCODE) { throw "Flashing failed." }
Write-Host "Flashed $Target merged image at 0x0 on $Port"
