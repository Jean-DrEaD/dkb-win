$ErrorActionPreference = 'Stop'
Set-Location C:\NS2\dkb-pc-recomp
.\.venv\Scripts\python.exe -m installer `
  --exefs "C:\NS2\dkb-pc-recomp\game\exefs" `
  --romfs "C:\NS2\dkb-pc-recomp\game\romfs" `
  --dest "C:\NS2\Donkey Kong Bananza" `
  --toolchain "C:\msys64\clang64" `
  --deps "C:\msys64\clang64" `
  --ninja "C:\msys64\clang64\bin\ninja.exe" `
  --dll-dir "C:\msys64\clang64\bin" `
  --dotnet "C:\Program Files\dotnet\dotnet.EXE" `
  --lang pt-BR
if ($LASTEXITCODE -ne 0) { throw "Installer falhou (codigo $LASTEXITCODE)" }
"BUILD OK"
