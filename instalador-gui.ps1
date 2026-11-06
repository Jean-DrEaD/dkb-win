Add-Type -AssemblyName System.Windows.Forms
$root = $PSScriptRoot
$f = New-Object Windows.Forms.Form
$f.Text = "dkb-win - Instalador"; $f.Size = '520,250'; $f.StartPosition = 'CenterScreen'
function Linha($txt, $y) {
  $l = New-Object Windows.Forms.Label; $l.Text = $txt; $l.Location = "10,$y"; $l.AutoSize = $true; $f.Controls.Add($l)
  $t = New-Object Windows.Forms.TextBox; $t.Location = "10,$($y+20)"; $t.Width = 380; $f.Controls.Add($t)
  $b = New-Object Windows.Forms.Button; $b.Text = "Procurar"; $b.Location = "400,$($y+18)"; $f.Controls.Add($b)
  $b.Add_Click({ $d = New-Object Windows.Forms.FolderBrowserDialog; if ($d.ShowDialog() -eq 'OK') { $t.Text = $d.SelectedPath } }.GetNewClosure())
  return $t
}
$ex = Linha "Pasta ExeFS (versao base 1.0.0):" 10
$ro = Linha "Pasta RomFS:" 60
$go = New-Object Windows.Forms.Button; $go.Text = "Compilar"; $go.Location = "10,120"; $go.Size = '480,40'; $f.Controls.Add($go)
$go.Add_Click({
  if (-not (Test-Path "C:\msys64\clang64\bin")) { [Windows.Forms.MessageBox]::Show("MSYS2 clang64 nao encontrado em C:\msys64. Instale antes (ver README)."); return }
  if (-not (Test-Path (Join-Path $ex.Text "main"))) { [Windows.Forms.MessageBox]::Show("ExeFS invalida: falta o arquivo 'main'."); return }
  if (-not (Test-Path $ro.Text)) { [Windows.Forms.MessageBox]::Show("Escolha a pasta RomFS."); return }
  $g = Join-Path $root "game"
  New-Item -ItemType Directory -Force "$g\exefs","$g\romfs" | Out-Null
  Copy-Item "$($ex.Text)\*" "$g\exefs" -Recurse -Force
  Copy-Item "$($ro.Text)\*" "$g\romfs" -Recurse -Force
  Start-Process powershell -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-File","`"$root\build-dkb.ps1`"" -WorkingDirectory $root
  [Windows.Forms.MessageBox]::Show("Compilacao iniciada (cerca de 25 min). Acompanhe a janela do PowerShell.")
  $f.Close()
})
[void]$f.ShowDialog()
