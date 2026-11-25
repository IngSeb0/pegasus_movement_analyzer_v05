$ErrorActionPreference = 'Stop'
$candidate = Join-Path $PSScriptRoot 'candidato_defensa.pptx'
$render = Join-Path $PSScriptRoot 'render_powerpoint'
New-Item -ItemType Directory -Force -Path $render | Out-Null
$wasOpen = Get-Process -Name POWERPNT -ErrorAction SilentlyContinue
$powerpoint = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    $presentation = $powerpoint.Presentations.Open($candidate, -1, 0, 0)
    if ($presentation.Slides.Count -ne 17) {
        throw 'Expected 17 slides.'
    }
    for ($i = 1; $i -le $presentation.Slides.Count; $i++) {
        $image = Join-Path $render ('{0:00}.png' -f $i)
        $presentation.Slides.Item($i).Export($image, 'PNG', 1280, 720)
    }
    Write-Output "PowerPoint opened and rendered all 17 slides."
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if (-not $wasOpen -and $powerpoint.Presentations.Count -eq 0) {
        $powerpoint.Quit()
    }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerpoint)
}
