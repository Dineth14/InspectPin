param([string]$Destination = "$PSScriptRoot\..\dist\revn")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$destinationPath = [System.IO.Path]::GetFullPath($Destination)
if (!$destinationPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Destination must stay inside the repository." }
New-Item -ItemType Directory -Force $destinationPath | Out-Null
$sourceZip = Join-Path $destinationPath "InspectPin_RevN_Complete_Source.zip"
$fctZip = Join-Path $destinationPath "InspectPin_RevN_JLCPCB_Firmware_FCT_Package.zip"
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$sourceStage = Join-Path $destinationPath "source_stage_$stamp"
$fctStage = Join-Path $destinationPath "fct_stage_$stamp"
New-Item -ItemType Directory $sourceStage,$fctStage | Out-Null
try {
  $sourceDirs = @('assets','backend','docs','firmware','hardware','mobile_app','REV N','scripts','simulator','web','manufacturing')
  foreach ($dir in $sourceDirs) {
    $target = Join-Path $sourceStage $dir
    New-Item -ItemType Directory -Force $target | Out-Null
    & robocopy (Join-Path $root $dir) $target /E /NFL /NDL /NJH /NJS /NP /XD node_modules dist .dart_tool build __pycache__ .pytest_cache .ruff_cache data models reports | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "Copy failed for $dir ($LASTEXITCODE)." }
  }
  Copy-Item "$root\README.md","$root\pytest.ini","$root\docker-compose.yml","$root\.gitignore" $sourceStage
  New-Item -ItemType Directory -Force "$fctStage\firmware","$fctStage\docs","$fctStage\REV N" | Out-Null
  Copy-Item "$root\manufacturing\*" $fctStage -Recurse -Force -Exclude package_revn.ps1,reports
  Copy-Item "$root\firmware\InspectPinFactoryTest" "$fctStage\firmware" -Recurse -Force
  Copy-Item "$root\docs\REV_N_HARDWARE_AUDIT.md","$root\docs\REV_N_JLCPCB_HANDOFF.md","$root\docs\REV_N_BUILD_REPORT.md","$root\docs\REV_N_COMPLETION_REPORT.md" "$fctStage\docs"
  Copy-Item "$root\REV N\fabrication" "$fctStage\REV N" -Recurse -Force
  if (Test-Path $sourceZip) { Remove-Item -LiteralPath $sourceZip }
  if (Test-Path $fctZip) { Remove-Item -LiteralPath $fctZip }
  # bsdtar handles the supplied nested fabrication ZIPs reliably; PowerShell's
  # Compress-Archive can lock a nested archive while enumerating it.
  & tar.exe -a -cf $sourceZip -C $sourceStage .
  if ($LASTEXITCODE) { throw "Source archive creation failed." }
  & tar.exe -a -cf $fctZip -C $fctStage .
  if ($LASTEXITCODE) { throw "FCT archive creation failed." }
  Get-FileHash $sourceZip,$fctZip -Algorithm SHA256 | ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), $_.Path.Substring($destinationPath.Length + 1) } | Set-Content (Join-Path $destinationPath 'SHA256SUMS.txt')
} finally {
  if (Test-Path $sourceStage) { Remove-Item -LiteralPath $sourceStage -Recurse -Force }
  if (Test-Path $fctStage) { Remove-Item -LiteralPath $fctStage -Recurse -Force }
}
Write-Host "Created $sourceZip"
Write-Host "Created $fctZip"
