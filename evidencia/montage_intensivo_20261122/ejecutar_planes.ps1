param([Parameter(Mandatory)][string]$SshConfig)
$ErrorActionPreference = 'Stop'
$phase = '/mnt/montage_intensivo_20261122/planes'
$results = Join-Path $PSScriptRoot 'RESULTADOS'

& ssh -F $SshConfig dme-master "sudo -n install -d -o dmeadmin -g dmeadmin $phase"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el directorio de planes' }
& scp -F $SshConfig "$PSScriptRoot/preparacion_planes.tar.gz" "$PSScriptRoot/exportar_nativo.py" "$results/mosaico.hdr" "$results/ENTRADAS.json" "dme-master:$phase/"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo copiar el paquete de planes' }
& ssh -F $SshConfig dme-master "cd $phase && tar -xzf preparacion_planes.tar.gz && cp ~/montage_intensivo_20261122/entradas_sia/*.fits montage_assets/ && cp mosaico.hdr montage_assets/template.hdr && python3 -u design_sia.py && python3 -u planificar_sia.py"
$phaseExit = $LASTEXITCODE
& ssh -F $SshConfig dme-master "cd $phase && python3 exportar_nativo.py"
if ($LASTEXITCODE -eq 0) {
    & scp -F $SshConfig "dme-master:$phase/evidencia.tar.gz" "$results/planes_nativos.tar.gz"
}
if ($phaseExit -ne 0) { throw "El cotejo de planes terminó con código $phaseExit" }
foreach ($name in @('SPECS.json', 'REFERENCE.json', 'PLAN_ACCOUNTS.json', 'PREDICCIONES.json', 'DISENO_CONGELADO.json')) {
    & scp -F $SshConfig "dme-master:$phase/$name" $results
    if ($LASTEXITCODE -ne 0) { throw "No se pudo recuperar $name" }
}
