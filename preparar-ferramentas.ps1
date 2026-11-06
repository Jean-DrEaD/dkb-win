$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = "Tls12"
$tmp = Join-Path $env:TEMP "dkb-ferramentas"; New-Item -ItemType Directory -Force $tmp | Out-Null
Start-Transcript (Join-Path $PSScriptRoot "ferramentas.log") -Force | Out-Null
function Passo($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }

Passo "MSYS2 (clang64)"
$msys = "C:\msys64"; $bash = "$msys\usr\bin\bash.exe"
if (-not (Test-Path $bash)) {
  Write-Host "Baixando MSYS2..."
  Invoke-WebRequest "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-x86_64-latest.exe" -OutFile "$tmp\msys2.exe"
  & "$tmp\msys2.exe" in --confirm-command --accept-messages --root C:/msys64 | Out-Host
  & $bash -lc "pacman -Syu --noconfirm" | Out-Host
}
& $bash -lc "pacman -Syu --noconfirm" | Out-Host
$pk = "clang lld sdl3 opus zstd ninja" -split " " | ForEach-Object { "mingw-w64-clang-x86_64-$_" }
& $bash -lc "pacman -S --needed --noconfirm $($pk -join ' ')" | Out-Host
if ($LASTEXITCODE) { throw "pacman falhou" }

Passo "Python 3.12"
$py = $null
foreach ($c in "py","python") { try { & $c -c "import sys" 2>$null; if (-not $LASTEXITCODE) { $py = $c; break } } catch {} }
if (-not $py) {
  Write-Host "Baixando Python..."
  Invoke-WebRequest "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -OutFile "$tmp\python.exe"
  Start-Process "$tmp\python.exe" "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1" -Wait
  $env:Path = [Environment]::GetEnvironmentVariable("Path","User") + ";" + $env:Path
  $py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
}
foreach ($r in "tools\requirements.txt","launcher\requirements.txt") {
  $f = Join-Path $PSScriptRoot $r
  if (Test-Path $f) { & $py -m pip install --user -q -r $f | Out-Host }
}

Passo ".NET SDK 8"
$hasNet = $false
try { if ((& dotnet --list-sdks 2>$null) -match "^8\.") { $hasNet = $true } } catch {}
if (-not $hasNet) {
  Invoke-WebRequest "https://dot.net/v1/dotnet-install.ps1" -OutFile "$tmp\dotnet-install.ps1"
  $dn = "$env:LOCALAPPDATA\Microsoft\dotnet"
  & "$tmp\dotnet-install.ps1" -Channel 8.0 -InstallDir $dn | Out-Host
  $u = [Environment]::GetEnvironmentVariable("Path","User")
  if ($u -notlike "*$dn*") { [Environment]::SetEnvironmentVariable("Path", "$dn;$u", "User") }
  $env:Path = "$dn;$env:Path"
}

Write-Host "`nFerramentas prontas." -ForegroundColor Green
Stop-Transcript | Out-Null
