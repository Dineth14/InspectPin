param(
  [string]$Port = 'COM7',
  [string]$Output = '.build\physical-video.avi'
)
$serial = [System.IO.Ports.SerialPort]::new($Port, 115200, 'None', 8, 'One')
$serial.ReadTimeout = 1000
$serial.Open()
try {
  $serial.DiscardInBuffer()
  $serial.Write('g')
  $header = $null
  $deadline = [DateTime]::UtcNow.AddSeconds(10)
  while ([DateTime]::UtcNow -lt $deadline -and -not $header) {
    try {
      $line = $serial.ReadLine().Trim()
      if ($line.StartsWith('MEDIA_BINARY_BEGIN ')) { $header = $line }
    } catch [System.TimeoutException] {}
  }
  if (-not $header -or $header -notmatch 'size=(\d+) path=(.+)$') { throw 'Media header was not received' }
  $expected = [int64]$Matches[1]
  $remote = $Matches[2]
  $target = [System.IO.Path]::GetFullPath($Output)
  [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) | Out-Null
  $stream = [System.IO.File]::Open($target, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
  try {
    $buffer = New-Object byte[] 4096
    $received = [int64]0
    $deadline = [DateTime]::UtcNow.AddSeconds(120)
    while ($received -lt $expected -and [DateTime]::UtcNow -lt $deadline) {
      $want = [Math]::Min($buffer.Length, $expected - $received)
      try { $got = $serial.Read($buffer, 0, [int]$want) } catch [System.TimeoutException] { continue }
      if ($got -gt 0) { $stream.Write($buffer, 0, $got); $received += $got }
    }
  } finally { $stream.Dispose() }
  if ($received -ne $expected) { throw "Incomplete transfer: $received of $expected bytes" }
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
  "Downloaded $remote -> $target bytes=$received sha256=$hash"
} finally { $serial.Close() }
