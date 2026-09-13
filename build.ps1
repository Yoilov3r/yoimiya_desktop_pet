$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name "YoimiyaDesktopPet" `
    --icon "assets\poses\pet.ico" `
    --add-data "assets;assets" `
    "app.py"

Write-Host ""
Write-Host "Build complete: $ProjectRoot\dist\YoimiyaDesktopPet\YoimiyaDesktopPet.exe"
