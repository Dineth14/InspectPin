param([Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port)
$ErrorActionPreference='Stop'
$ssid=Read-Host 'Wi-Fi SSID'
$origin=(Read-Host 'Receiver origin, including http:// or https://').TrimEnd('/')
$pass=Read-Host 'Wi-Fi password' -AsSecureString
$token=Read-Host 'Device credential (Enter to keep existing for same origin)' -AsSecureString
$serial=[System.IO.Ports.SerialPort]::new($Port,115200)
$serial.Encoding=[Text.UTF8Encoding]::new($false)
$serial.ReadTimeout=1200
function Wait-Line([string]$pattern,[int]$seconds) {
    $deadline=[DateTime]::UtcNow.AddSeconds($seconds)
    while([DateTime]::UtcNow -lt $deadline) {
        try { $line=$serial.ReadLine().Trim(); if($line -match $pattern){return $line} }
        catch [TimeoutException] {}
    }
    throw 'Board did not acknowledge. Confirm the board is awake, idle, and running the evaluation firmware.'
}
try {
    $serial.Open()
    $serial.DiscardInBuffer()
    $serial.Write('@')
    $null=Wait-Line '^IP_SETUP_READY$' 10
    $record=@{ssid=$ssid; origin=$origin;password=[Net.NetworkCredential]::new('',$pass).Password; token=[Net.NetworkCredential]::new('',$token).Password}
    $serial.WriteLine(($record | ConvertTo-Json -Compress))
    $result=Wait-Line '^IP_SETUP_(SAVED|REJECTED|INVALID)$' 65
    Write-Host $result
    if($result -ne 'IP_SETUP_SAVED'){exit 1}
} finally {$serial.Dispose(); $pass.Dispose(); $token.Dispose()}
