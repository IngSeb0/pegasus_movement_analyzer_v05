param([ValidateSet('preflight','reanudar','calibrar','ssh','start','close','guard')] [string]$Action)
$ErrorActionPreference='Stop'
$root = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content -Raw "$root/azure_cloud_20261025/cluster.json" | ConvertFrom-Json
$receipt = Join-Path $PSScriptRoot 'ronda2_50mbit/sesion09'
New-Item -ItemType Directory -Force $receipt | Out-Null

function Azure {
    $result = & az @args --subscription $cfg.subscriptionId --only-show-errors -o json
    if ($LASTEXITCODE -ne 0) { throw "Azure falló en $($args[0]) $($args[1])" }
    $result
}

function Close-Session {
    $names = @('dme-master','dme-worker1','dme-worker2','dme-worker3','dme-worker4')
    foreach ($name in $names) {
        try { Azure vm deallocate -g $cfg.resourceGroup -n $name --no-wait | Out-Null }
        catch { Write-Warning $_ }
    }
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        $raw=Azure vm list -g $cfg.resourceGroup -d --query "[].{name:name,state:powerState}"
        $state=$raw | ConvertFrom-Json
        if (@($state).Count -eq 5 -and @($state | Where-Object state -ne 'VM deallocated').Count -eq 0) {
            $raw | Set-Content -Encoding utf8 "$receipt/estado_final.json"
            (Get-Date).ToUniversalTime().ToString('o') | Set-Content "$receipt/cierre_utc.txt"
            if (Test-Path "$receipt/regla_temporal.json") {
                $rule = Get-Content "$receipt/regla_temporal.json" -Raw | ConvertFrom-Json
                $rules = Azure network nsg rule list -g $cfg.resourceGroup --nsg-name $rule.nsg | ConvertFrom-Json
                if ($rules.name -contains $rule.name) {
                    Azure network nsg rule delete -g $cfg.resourceGroup --nsg-name $rule.nsg -n $rule.name | Out-Null
                }
                (Get-Date).ToUniversalTime().ToString('o') | Set-Content "$receipt/regla_retirada_utc.txt"
            }
            return
        }
        Start-Sleep -Seconds 5
    }
    throw 'Desasignación aún sin confirmar'
}

if ($Action -eq 'close') { Close-Session; exit }
if ($Action -eq 'start') {
    if (Test-Path "$receipt/inicio_utc.txt") { throw 'Sesion ya iniciada' }
    $start=[datetimeoffset]::UtcNow
    $start.ToString('o') | Set-Content "$receipt/inicio_utc.txt"
    $start.AddSeconds(14857).ToString('o') | Set-Content "$receipt/limite_utc.txt"
    Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-File',$PSCommandPath,'guard') -WindowStyle Hidden
    for ($i=0; $i -lt 30 -and !(Test-Path "$receipt/guardia_lista.txt"); $i++) { Start-Sleep 1 }
    if (!(Test-Path "$receipt/guardia_lista.txt")) { throw "Guardia sin confirmar" }
    try {
        foreach ($name in @('dme-master','dme-worker1','dme-worker2','dme-worker3','dme-worker4')) {
            Azure vm start -g $cfg.resourceGroup -n $name --no-wait | Out-Null
        }
        for ($attempt=0; $attempt -lt 90; $attempt++) {
            $state=Azure vm list -g $cfg.resourceGroup -d --query "[].{name:name,state:powerState}" | ConvertFrom-Json
            if (@($state | Where-Object state -eq 'VM running').Count -eq 5) { exit }
            Start-Sleep 5
        }
        throw 'El arranque sigue pendiente'
    } catch { Close-Session; throw }
    exit
}
if ($Action -eq 'reanudar') {
    if (Test-Path "$receipt/inicio_utc.txt") { throw 'Ya existe la segunda sesión' }
    Copy-Item -LiteralPath "$PSScriptRoot/sesion_original/cotejo_azure.json" -Destination "$receipt/cotejo_azure.json"
    $start=[datetimeoffset]::UtcNow
    $start.ToString('o') | Set-Content "$receipt/inicio_utc.txt"
    $start.AddSeconds(14857).ToString('o') | Set-Content "$receipt/limite_utc.txt"
    Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-File',"`"$PSCommandPath`"",'guard') -WindowStyle Hidden
    for ($i=0; $i -lt 30 -and !(Test-Path "$receipt/guardia_lista.txt"); $i++) { Start-Sleep 1 }
    if (!(Test-Path "$receipt/guardia_lista.txt")) { throw 'Guardia sin confirmar' }
    try { Azure vm start -g $cfg.resourceGroup -n dme-master --no-wait | Out-Null }
    catch { Close-Session; throw }
    $Action='calibrar'
}
if ($Action -eq 'ssh') {
    if (!(Test-Path "$receipt/inicio_utc.txt") -or (Test-Path "$receipt/cierre_utc.txt")) { throw 'No hay sesión abierta' }
    $nsgs = Azure network nsg list -g $cfg.resourceGroup | ConvertFrom-Json
    $eligible = @($nsgs | Where-Object { $_.securityRules.destinationPortRange -contains '22' })
    if ($eligible.Count -ne 1) { throw 'No se identificó el NSG de administración' }
    $nsg = $eligible[0].name
    $ip = (Invoke-RestMethod 'https://api.ipify.org' -TimeoutSec 15).Trim()
    $address = [ipaddress]::Parse($ip)
    if ($address.AddressFamily -ne 'InterNetwork') { throw 'Se requiere una dirección IPv4 de origen' }
    $master = Azure vm show -d -g $cfg.resourceGroup -n dme-master | ConvertFrom-Json
    $priority = 111..199 | Where-Object { $_ -notin $eligible[0].securityRules.priority } | Select-Object -First 1
    $name = 'DME-montage-intensivo-20261122-s09-ssh'
    if (!$priority -or $eligible[0].securityRules.name -contains $name) { throw 'Colisión de regla temporal' }
    @{nsg=$nsg;name=$name} | ConvertTo-Json | Set-Content "$receipt/regla_temporal.json"
    $command='install -d -m 0755 /run/sshd && systemd-run --unit=dme-montage-intensivo-s09-ssh --property=RuntimeMaxSec=14857 /usr/sbin/sshd -D -e -p 443 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o PermitRootLogin=no -o AllowUsers=dmeadmin -o PidFile=/run/dme-montage-intensivo-s09-ssh.pid'
    Azure vm run-command invoke -g $cfg.resourceGroup -n dme-master --command-id RunShellScript --scripts $command | Out-Null
    Azure network nsg rule create -g $cfg.resourceGroup --nsg-name $nsg -n $name --priority $priority --direction Inbound --access Allow --protocol Tcp --source-address-prefixes "$ip/32" --destination-address-prefixes "$($master.privateIps)/32" --destination-port-ranges 443 | Out-Null
    $key = (Resolve-Path "$root/azure_cloud_20261025/.local/id_ed25519_dme").Path.Replace('\','/')
    @("Host dme-master","  HostName $($master.publicIps)","  Port 443","  User dmeadmin","  IdentityFile $key","  BatchMode yes","  ConnectTimeout 12","  StrictHostKeyChecking accept-new") | Set-Content -Encoding ascii "$receipt/ssh_config"
    exit
}
if ($Action -eq 'calibrar') {
    if (!(Test-Path "$receipt/cotejo_azure.json") -or (Test-Path "$receipt/cierre_utc.txt") -or (Test-Path "$receipt/calibracion_azure.json")) { throw 'La sesión no admite calibración' }
    $previous = ((Get-Content "$receipt/cotejo_azure.json" -Raw | ConvertFrom-Json).value | ForEach-Object message) -join "`n"
    if ([regex]::Matches($previous,'"coincide": true').Count -ne 3) { throw 'Cotejo nativo incompleto' }
    try {
        foreach ($index in 2..4) { Azure vm start -g $cfg.resourceGroup -n "dme-worker$index" --no-wait | Out-Null }
        Azure vm start -g $cfg.resourceGroup -n dme-worker1 | Out-Null
        Start-Sleep 20
        $response = Azure vm run-command invoke -g $cfg.resourceGroup -n dme-worker1 --command-id RunShellScript --scripts "@$PSScriptRoot/calibrar.sh"
        $response | Set-Content -Encoding utf8 "$receipt/calibracion_azure.json"
        $message = (($response | ConvertFrom-Json).value | ForEach-Object message) -join "`n"
        Write-Output $message
        $line = [regex]::Match($message,'(?m)^DME_CALIBRATION (\{[^\r\n]+\})')
        if (!$line.Success) { throw 'Falta el registro de calibración' }
        $entry = $line.Groups[1].Value | ConvertFrom-Json -AsHashtable
        $line.Groups[1].Value | Set-Content -Encoding utf8 "$PSScriptRoot/calibracion.json"
        if (!$entry.N) { throw 'No se fijó N dentro del intervalo autorizado' }
        (Get-Date).ToUniversalTime().ToString('o') | Set-Content "$receipt/workers_y_calibracion_utc.txt"
    } catch {
        Close-Session
        throw
    }
    exit
}
if ($Action -eq 'guard') {
    (Get-Date).ToUniversalTime().ToString('o') | Set-Content "$receipt/guardia_lista.txt"
    $deadline = [datetimeoffset]::Parse((Get-Content "$receipt/limite_utc.txt" -Raw))
    while ([datetimeoffset]::UtcNow -lt $deadline.AddMinutes(-15)) {
        if (Test-Path "$receipt/cierre_utc.txt") { exit }
        Start-Sleep 10
    }
    Close-Session
    exit
}

if (Test-Path "$receipt/inicio_utc.txt") { throw 'La sesión ya tiene un inicio registrado' }
$state = Azure vm list -g $cfg.resourceGroup -d --query "[].{name:name,state:powerState}" | ConvertFrom-Json
if (@($state).Count -ne 5 -or @($state | Where-Object state -ne 'VM deallocated').Count -ne 0) {
    throw 'La sesión requiere confirmar el estado inicial de las cinco VMs'
}
$start=[datetimeoffset]::UtcNow
$start.ToString('o') | Set-Content "$receipt/inicio_utc.txt"
$start.AddSeconds(14857).ToString('o') | Set-Content "$receipt/limite_utc.txt"
Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-File',"`"$PSCommandPath`"",'guard') -WindowStyle Hidden
for ($i=0; $i -lt 30 -and !(Test-Path "$receipt/guardia_lista.txt"); $i++) { Start-Sleep 1 }
if (!(Test-Path "$receipt/guardia_lista.txt")) { throw 'No se confirmó la guardia. VMs sin iniciar.' }
try {
    Azure vm start -g $cfg.resourceGroup -n dme-master | Out-Null
    $response = Azure vm run-command invoke -g $cfg.resourceGroup -n dme-master --command-id RunShellScript --scripts "@$PSScriptRoot/preflight_azure.sh"
    $response | Set-Content -Encoding utf8 "$receipt/cotejo_azure.json"
    $message = (($response | ConvertFrom-Json).value | ForEach-Object message) -join "`n"
    Write-Output $message
    if ([regex]::Matches($message,'"coincide": true').Count -ne 3) { throw 'No se confirmaron los tres cotejos nativos' }
} catch {
    Close-Session
    throw
}
