$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$py = "$PSScriptRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Ambiente Python nao encontrado. Rode o Instalar.bat primeiro." }
$dotnet = @(
  (Get-Command dotnet -ErrorAction SilentlyContinue).Source,
  "$env:LOCALAPPDATA\Microsoft\dotnet\dotnet.exe",
  "C:\Program Files\dotnet\dotnet.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $dotnet) { throw ".NET SDK 8 nao encontrado. Rode o Instalar.bat primeiro." }
$cl = "C:\msys64\clang64"
if (-not (Test-Path "$cl\bin\clang.exe")) { throw "MSYS2 clang64 nao encontrado. Rode o Instalar.bat primeiro." }
& $py -m installer `
  --exefs "$PSScriptRoot\game\exefs" `
  --romfs "$PSScriptRoot\game\romfs" `
  --dest "$PSScriptRoot\jogo" `
  --toolchain $cl `
  --deps $cl `
  --ninja "$cl\bin\ninja.exe" `
  --dll-dir "$cl\bin" `
  --dotnet $dotnet `
  --lang pt-BR
if ($LASTEXITCODE -ne 0) { throw "Installer falhou (codigo $LASTEXITCODE)" }
"BUILD OK"
