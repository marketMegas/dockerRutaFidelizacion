[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'build', 'down', 'restart', 'ps', 'logs', 'health', 'e2e', 'dev-panel', 'dev-pwa', 'connector', 'help')]
    [string]$Accion = 'help',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Resto
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$ApiUrl = if ($env:VITE_API_URL) { $env:VITE_API_URL } else { 'http://127.0.0.1:8002/fid-api' }
$Base = 'http://127.0.0.1:8002/fid-api'
$Json = 'application/json'

function Show-Help {
    Write-Host "Uso: .\dev.ps1 <accion> [extra]"
    Write-Host ""
    Write-Host "  up                Construye y levanta todo (docker compose up -d --build)"
    Write-Host "  build             Solo construye las imagenes"
    Write-Host "  down              Baja los contenedores"
    Write-Host "  restart [servicio]  Reinicia (todos o uno)"
    Write-Host "  ps                Estado de los contenedores"
    Write-Host "  logs [servicio]   Sigue los logs (Ctrl+C para salir)"
    Write-Host "  health            Verifica API, panel, PWA y sus proxys"
    Write-Host "  e2e               Flujo completo por API (cliente, venta, duplicado, canje, admin)"
    Write-Host "  dev-panel         Panel en modo desarrollo (Vite HMR, puerto 5174)"
    Write-Host "  dev-pwa           PWA en modo desarrollo (Vite HMR, puerto 5175)"
    Write-Host "  connector <...>   Conector dentro de Docker (ej: connector simular --litros 20 --placa ABC123 --telefono 3001234567)"
    Write-Host ""
    Write-Host "  API_URL por defecto: $ApiUrl"
}

switch ($Accion) {
    'up' { docker compose up -d --build }

    'build' { docker compose build }

    'down' { docker compose down }

    'restart' { docker compose restart @Resto }

    'ps' { docker compose ps }

    'logs' { docker compose logs -f @Resto }

    'health' {
        $checks = @(
            @{ Nombre = 'API';        Url = 'http://127.0.0.1:8002/health' },
            @{ Nombre = 'Panel';      Url = 'http://127.0.0.1:5139/panel/' },
            @{ Nombre = 'PWA';        Url = 'http://127.0.0.1:5140/' },
            @{ Nombre = 'Panel->API'; Url = 'http://127.0.0.1:5139/fid-api/health' },
            @{ Nombre = 'PWA->API';   Url = 'http://127.0.0.1:5140/fid-api/health' }
        )
        foreach ($c in $checks) {
            try {
                $r = Invoke-WebRequest -Uri $c.Url -UseBasicParsing -TimeoutSec 5
                Write-Host ("{0,-12} OK   {1}" -f $c.Nombre, $r.StatusCode)
            }
            catch {
                Write-Host ("{0,-12} ERR  {1}" -f $c.Nombre, $_.Exception.Message)
            }
        }
    }

    'e2e' {
        $telefono = '3001234567'
        $placa = 'ABC123'
        $factura = "E2E-$([int](Get-Date -UFormat %s))"

        $otp = Invoke-RestMethod -Method Post -Uri "$Base/auth/otp/request" -ContentType $Json -Body (@{ placa = $placa; telefono = $telefono; cedula = '1098765432'; nombre = 'Juan E2E' } | ConvertTo-Json)
        Write-Host "OTP solicitado (cliente_nuevo=$($otp.cliente_nuevo), celular=$($otp.telefono_parcial))"

        Write-Host "Enviando venta por el conector (dentro de Docker)..."
        docker compose run --rm --no-deps connector python conector.py simular --litros 20 --placa $placa --telefono $telefono --factura $factura

        Write-Host "Reenviando la misma factura (idempotencia)..."
        docker compose run --rm --no-deps connector python conector.py simular --litros 20 --placa $placa --telefono $telefono --factura $factura

        $otp2 = Invoke-RestMethod -Method Post -Uri "$Base/auth/otp/request" -ContentType $Json -Body (@{ placa = $placa } | ConvertTo-Json)
        $ver = Invoke-RestMethod -Method Post -Uri "$Base/auth/otp/verify" -ContentType $Json -Body (@{ placa = $placa; codigo = $otp2.debug_codigo } | ConvertTo-Json)
        Write-Host "Saldo del cliente placa=$($ver.cliente.placa): $($ver.cliente.puntos) puntos"

        $adm = Invoke-RestMethod -Method Post -Uri "$Base/auth/admin" -ContentType $Json -Body (@{ usuario = 'admin'; password = 'admin123' } | ConvertTo-Json)
        $headers = @{ Authorization = "Bearer $($adm.access_token)" }
        $res = Invoke-RestMethod -Uri "$Base/admin/resumen" -Headers $headers
        Write-Host "Resumen -> clientes=$($res.total_clientes) ventas_hoy=$($res.ventas_hoy.cantidad) litros=$($res.ventas_hoy.litros) puntos_activos=$($res.puntos_activos)"

        $cli = Invoke-RestMethod -Uri "$Base/admin/clientes?q=$placa" -Headers $headers
        Write-Host "Cliente -> placa=$($cli.clientes[0].placa) cedula=$($cli.clientes[0].cedula) puntos=$($cli.clientes[0].puntos)"
    }

    'dev-panel' {
        Push-Location panel
        try {
            $env:VITE_API_URL = $ApiUrl
            npm run dev
        }
        finally { Pop-Location }
    }

    'dev-pwa' {
        Push-Location pwa
        try {
            $env:VITE_API_URL = $ApiUrl
            npm run dev
        }
        finally { Pop-Location }
    }

    'connector' {
        docker compose run --rm --no-deps connector python conector.py @Resto
    }

    'help' { Show-Help }
}
