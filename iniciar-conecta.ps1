# Script de inicio de Prebel Conecta (PowerShell)
# Levanta el backend (API de RRHH) y sirve la página de dist/index.html.
# Uso: .\iniciar-conecta.ps1  [-Puerto 8080] [-Verbose]
# (Nota: el bot.py de la raíz del proyecto tiene su propio iniciar.ps1 --
#  distinto nombre a propósito para no confundirlos.)

[CmdletBinding()]
param(
    [int]$Puerto = 8080
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = "$PSScriptRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    # Compatibilidad con un .venv compartido en la carpeta padre (como en esta
    # máquina de desarrollo); cualquier otro clon del repo no tendrá esa carpeta.
    $python = "$PSScriptRoot\..\.venv\Scripts\python.exe"
}
if (-not (Test-Path $python)) {
    Write-Host "No se encontró el entorno virtual (.venv) en prebel-conecta\ ni en su carpeta padre."
    Write-Host "Créalo desde prebel-conecta\ con:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

$backendUrl = "http://127.0.0.1:5000"
$replyUrl = "$backendUrl/reply"
$siteUrl = "http://127.0.0.1:$Puerto/index.html"
$backendLog = "$PSScriptRoot\backend.log"

Write-Host "Iniciando backend (API de RRHH) en $backendUrl ..."
$backend = Start-Process -FilePath $python -ArgumentList "model\rrhh_api.py" `
    -WorkingDirectory $PSScriptRoot -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "NUL" -RedirectStandardError $backendLog

Write-Host "Sirviendo la página en $siteUrl ..."
$server = Start-Process -FilePath $python -ArgumentList "-m", "http.server", "$Puerto", "--directory", "dist" `
    -WorkingDirectory $PSScriptRoot -PassThru -WindowStyle Hidden

$listo = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 1
    if ($backend.HasExited) {
        Write-Host "El backend se cerró inesperadamente. Revisa $backendLog para ver el error."
        break
    }
    Write-Verbose "[$i/30] Probando $replyUrl ..."
    try {
        Invoke-WebRequest -Uri $replyUrl -Method Post -Body '{"text":""}' -ContentType "application/json" -TimeoutSec 2 -ErrorAction Stop | Out-Null
        $listo = $true
        break
    } catch {
        Write-Verbose "[$i/30] $replyUrl aún no responde: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "URLs:"
Write-Host "  Sitio:          $siteUrl"
Write-Host "  Backend:        $backendUrl"
Write-Host "  Endpoint reply: $replyUrl"
Write-Host "  Log backend:    $backendLog"
if ($listo) {
    Write-Host "  Estado backend: listo"
} elseif ($backend.HasExited) {
    Write-Host "  Estado backend: se cerró inesperadamente (ver log)"
} else {
    Write-Host "  Estado backend: sin responder tras 30s (puede seguir descargando el modelo; ver log)"
}
Write-Host ""

Start-Process $siteUrl

Write-Host "Listo. Presiona Ctrl+C para detener el backend y la página."
try {
    Wait-Process -Id $backend.Id
}
finally {
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $server.Id -ErrorAction SilentlyContinue
}
