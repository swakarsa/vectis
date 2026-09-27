try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $presentation = $ppt.Presentations.Open("D:\vectis\docs\vectis-keynote-grand-finale.pptx", $false, $false, $false)
    $pdfPath = "D:\vectis\docs\vectis-keynote-grand-finale.pdf"
    # 32 = ppSaveAsPDF
    $presentation.SaveAs($pdfPath, 32)
    Write-Output "SUCCESS: Exported PPTX to PDF at $pdfPath"
    
    # Export slide images to assets/slides/pptx-slides/
    $outDir = "D:\vectis\assets\slides\pptx-slides"
    if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir }
    $i = 1
    foreach ($slide in $presentation.Slides) {
        $imgPath = "$outDir\slide-$i.png"
        $slide.Export($imgPath, "PNG", 1920, 1080)
        $i++
    }
    Write-Output "SUCCESS: Exported all slide PNGs to $outDir"
    
    $presentation.Close()
    $ppt.Quit()
} catch {
    Write-Output "ERROR or PowerPoint not installed: $_"
}
