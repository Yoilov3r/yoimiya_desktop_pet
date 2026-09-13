@echo off
if exist "%~dp0YoimiyaDesktopPet\YoimiyaDesktopPet.exe" (
    start "" "%~dp0YoimiyaDesktopPet\YoimiyaDesktopPet.exe"
) else if exist "%~dp0dist\YoimiyaDesktopPet\YoimiyaDesktopPet.exe" (
    start "" "%~dp0dist\YoimiyaDesktopPet\YoimiyaDesktopPet.exe"
) else (
    echo 未找到 YoimiyaDesktopPet.exe
    pause
)
