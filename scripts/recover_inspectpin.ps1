param(
    [Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port,
    [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$esptool="$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
$backup='.backups/local-release-20261124-194703'
$application="$backup/pre-sound-and-ota.bin"
$boot="$backup/pre-sound-boot-and-settings.bin"
$layout="$backup/pre-app.bin"
if ((Get-FileHash -LiteralPath $application).Hash -ne '4E31EDE49D819773A65469422A9F2E03991133D88408716D624EB70CCCAC596E' -or
    (Get-FileHash -LiteralPath $boot).Hash -ne 'A60CF4A5AB25D0AE391E6D92BBAF062D29C4DAD716E5F48C192927898AC241F0') {
    throw 'Private backup does not match the verified release'
}
$identity=& $esptool --chip esp32s3 --port $Port flash-id
$identity
if($LASTEXITCODE -ne 0 -or ($identity -join "`n") -notmatch '68:ee:8f:5c:22:dc' -or
   ($identity -join "`n") -notmatch 'Detected flash size: 8MB'){
    throw 'Board identity and flash size did not match the recovery record'
}
& $esptool --chip esp32s3 --port $Port verify-flash 0x0 $layout
if($LASTEXITCODE -ne 0){throw 'Existing bootloader or partition table changed'}
if($CheckOnly){return}
if((Read-Host 'Type RESTORE APP0 to restore the previous firmware on this board') -cne 'RESTORE APP0'){return}
$snapshot=[IO.File]::ReadAllBytes((Resolve-Path $boot))
$selection=[byte[]]::new(0x2000)
[Array]::Copy($snapshot,0xe000,$selection,0,0x2000)
$selectorPath=Join-Path (Resolve-Path $backup) 'recovery-otadata.bin'
[IO.File]::WriteAllBytes($selectorPath,$selection)
& $esptool --chip esp32s3 --port $Port --after no-reset-stub write-flash 0x10000 $application
if($LASTEXITCODE -ne 0){throw 'Application write failed'}
& $esptool --chip esp32s3 --port $Port --after no-reset-stub verify-flash 0x10000 $application
if($LASTEXITCODE -ne 0){throw 'Application verification failed'}
& $esptool --chip esp32s3 --port $Port --after no-reset-stub write-flash 0xe000 $selectorPath
if($LASTEXITCODE -ne 0){throw 'OTA selection write failed'}
& $esptool --chip esp32s3 --port $Port verify-flash 0xe000 $selectorPath
if($LASTEXITCODE -ne 0){throw 'OTA selection verification failed'}
