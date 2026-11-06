# Confere e corrige o ambiente MSYS2 CLANG64 antes do build.
$ErrorActionPreference = 'Stop'
$log = Join-Path $PSScriptRoot 'verificar-ambiente.log'
function Say($m) { Write-Host $m; Add-Content -Path $log -Value $m }
"=== $(Get-Date) ===" | Out-File $log

$msys = @('C:\msys64', "$env:SystemDrive\msys64") | Where-Object { Test-Path "$_\usr\bin\pacman.exe" } | Select-Object -First 1
if (-not $msys) { Say '[ERRO] MSYS2 nao encontrado / MSYS2 no encontrado / MSYS2 not found (C:\msys64). Rode preparar-ferramentas.ps1.'; exit 1 }
Say "MSYS2: $msys"

$pre = 'mingw-w64-clang-x86_64-'
$pkgs = 'clang','lld','sdl3','opus','zstd','ninja','vulkan-headers','vulkan-loader','pkgconf' | ForEach-Object { "$pre$_" }
$env:MSYSTEM = 'CLANG64'; $env:CHERE_INVOKING = '1'
$pacman = "$msys\usr\bin\pacman.exe"

$falta = $pkgs | Where-Object { & $pacman -Q $_ 2>$null | Out-Null; $LASTEXITCODE -ne 0 }
if ($falta) {
  Say "Instalando / Instalando / Installing: $($falta -join ' ')"
  & "$msys\usr\bin\bash.exe" -lc "pacman -Sy --needed --noconfirm $($falta -join ' ')" 2>&1 | ForEach-Object { Add-Content $log $_ }
}

$c = "$msys\clang64"
$arquivos = @(
  "$c\include\vulkan\vulkan.h", "$c\lib\libvulkan-1.dll.a",
  "$c\include\SDL3\SDL.h", "$c\include\opus\opus.h", "$c\include\zstd.h",
  "$c\bin\clang.exe", "$c\bin\ld.lld.exe", "$c\bin\ninja.exe"
)
$ruins = $arquivos | Where-Object { -not (Test-Path $_) }
if ($ruins) {
  Say '[ERRO] Ainda faltam / Aun faltan / Still missing:'
  $ruins | ForEach-Object { Say "   $_" }
  Say "Log: $log"
  exit 1
}

$livre = [math]::Round((Get-PSDrive ($PSScriptRoot.Substring(0,1))).Free / 1GB, 1)
if ($livre -lt 25) { Say "[AVISO] Pouco espaco / Poco espacio / Low disk: $livre GB (recomendado 25 GB)" }
if ($PSScriptRoot -match '[^\x20-\x7E]') { Say '[AVISO] Pasta com acento/caractere especial / Carpeta con tilde / Non-ASCII path. Prefira C:\dkb-win.' }

Say '[OK] Ambiente pronto / Entorno listo / Environment ready.'
exit 0
