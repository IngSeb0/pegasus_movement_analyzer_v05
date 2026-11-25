$ErrorActionPreference = 'Stop'
$config = Join-Path $PSScriptRoot 'sesion04/ssh_config'
$remote = '/mnt/montage_intensivo_20261122/sia'
$results = Join-Path $PSScriptRoot 'RESULTADOS'

function Check-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step falló con código $LASTEXITCODE" }
}

try {
    & powershell -NoProfile -File "$PSScriptRoot/control_sia.ps1" -Action ssh
    Check-Exit 'Habilitar acceso al coordinador'
    & ssh -F $config dme-master "sudo -n install -d -o dmeadmin -g dmeadmin $remote"
    Check-Exit 'Crear directorio de trabajo'
    $wheel = Get-ChildItem "$PSScriptRoot/../pruebas_cierre_sin_cf_20261031/preparacion_montage/*.whl" | Select-Object -First 1
    & scp -F $config "$PSScriptRoot/sia.py" "$PSScriptRoot/cabecera.py" $wheel.FullName "dme-master:$remote/"
    Check-Exit 'Copiar recolector'
    & ssh -F $config dme-master "cd $remote && python3 sia.py > DESCARGA_SIA.log 2>&1"
    $downloadExit = $LASTEXITCODE
    & scp -F $config "dme-master:$remote/DESCARGA_SIA.log" $results
    foreach ($name in @('SIA_2MASS_J.xml', 'SELECCION_SIA.json', 'ENTRADAS.json')) {
        & scp -F $config "dme-master:$remote/RESULTADOS/$name" $results
    }
    if ($downloadExit -ne 0) { throw "La consulta o descarga terminó con código $downloadExit" }
    & ssh -F $config dme-master "cd $remote && python3 -m zipfile -e $($wheel.Name) montagepy && PYTHONPATH=montagepy python3 cabecera.py"
    Check-Exit 'Construir la cabecera con Montage'
    & scp -F $config "dme-master:$remote/RESULTADOS/mosaico.hdr" $results
    Check-Exit 'Guardar la cabecera'
} finally {
    & powershell -NoProfile -File "$PSScriptRoot/control_sia.ps1" -Action close
    Check-Exit 'Desasignar y confirmar las VMs'
}
