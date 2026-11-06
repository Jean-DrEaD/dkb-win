# Verifica a versao no GitHub e atualiza o dkb-win (mantem game, jogo, .venv, build e logs).
$ErrorActionPreference = 'Stop'
$repo = 'Jean-DrEaD/dkb-win'
$here = $PSScriptRoot
if (Test-Path "$here\.git") { Write-Host '[update] Pasta git (desenvolvimento): auto-update ignorado. Use git pull.'; exit 0 }
$v = (Get-Content "$here\VERSION" -ErrorAction SilentlyContinue | Select-Object -First 1) -replace '[^\d.]',''
if (-not $v) { $v = '0.0.0' }
$local = [version]$v
try {
  [Net.ServicePointManager]::SecurityProtocol = 'Tls12'
  $h = @{ 'User-Agent' = 'dkb-win' }
  $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers $h -TimeoutSec 15
} catch { Write-Host '[update] Sem internet/GitHub -> seguindo com a versao atual / Sin conexion / Offline.'; exit 0 }
$remote = [version]($rel.tag_name.TrimStart('v'))
Write-Host "Versao instalada / instalada / installed: $local | ultima / ultima / latest: $remote"
if ($remote -le $local) { Write-Host '[OK] Atualizado / Actualizado / Up to date.'; exit 0 }
$r = Read-Host "Nova versao / Nueva version / New version $remote. Atualizar agora? / Actualizar? / Update? (S/n)"
if ($r -match '^[nN]') { exit 0 }
try {
  $tmp = Join-Path $env:TEMP 'dkb-win-update'
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory $tmp | Out-Null
  Write-Host 'Baixando / Descargando / Downloading...'
  Invoke-WebRequest $rel.zipball_url -OutFile "$tmp\u.zip" -Headers $h -UseBasicParsing
  Expand-Archive "$tmp\u.zip" "$tmp\x" -Force
  $src = (Get-ChildItem "$tmp\x" -Directory | Select-Object -First 1).FullName
  Copy-Item "$src\Instalar.bat" "$here\Instalar.bat.new" -Force
  robocopy $src $here /E /XD game jogo .venv build /XF Instalar.bat *.log /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy $LASTEXITCODE" }
} catch { Write-Host "[ERRO] Falha na atualizacao / Fallo / Update failed: $_ -> seguindo com a versao atual."; exit 0 }
Write-Host "[OK] Atualizado para / Actualizado a / Updated to $remote. Reiniciando..."
exit 2
