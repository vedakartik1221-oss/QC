try {
    $app = New-Object -ComObject PowerPoint.Application
    $presPath = (Get-Item "slides\QuantumScreen_Review_Presentation.pptx").FullName
    $app.Visible = 1
    $pres = $app.Presentations.Open($presPath, -1, 0, -1)
    Write-Host "Presentation opened successfully. Slide count:" $pres.Slides.Count
    
    $outDir = (Get-Item "slides").FullName + "\exported_slides"
    if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
    
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        $slide = $pres.Slides.Item($i)
        $outFile = "$outDir\slide_$i.png"
        $slide.Export($outFile, "PNG", 1920, 1080)
        Write-Host "Exported slide $i to $outFile"
    }
    
    $pres.Close()
    $app.Quit()
} catch {
    Write-Host "Error:" $_
}
