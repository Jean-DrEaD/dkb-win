$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
.\.venv\Scripts\python.exe -m installer `
  --exefs "$PSScriptRoot\game\exefs" `
  --romfs "$PSScriptRoot\game\romfs" `
  --dest "$PSScriptRoot\jogo" `
  --toolchain "C:\msys64\clang64" `
  --deps "C:\msys64\clang64" `
  --ninja "C:\msys64\clang64\bin\ninja.exe" `
  --dll-dir "C:\msys64\clang64\bin" `
  --dotnet "C:\Program Files\dotnet\dotnet.EXE" `
  --lang pt-BR
if ($LASTEXITCODE -ne 0) { throw "Installer falhou (codigo $LASTEXITCODE)" }
"BUILD OK"

