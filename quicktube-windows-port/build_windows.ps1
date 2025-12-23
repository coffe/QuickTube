# build_windows.ps1
# Byggscript för QuickTube (Windows Port)
# Kör detta script i PowerShell som administratör

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Bygger QuickTube (Windows Port)..." -ForegroundColor Cyan

# --- CLEANUP ---
if (Test-Path "venv") {
    if (-not (Test-Path "venv\Scripts\pip.exe")) {
        Write-Host "Rensar gammal venv..." -ForegroundColor Yellow
        Remove-Item "venv" -Recurse -Force
    }
}
if (-not (Test-Path "bin")) { New-Item -ItemType Directory -Force -Path "bin" | Out-Null }

# --- 1. PYTHON & SVTPLAY-DL ---
if (-not (Test-Path "venv")) {
    Write-Host "Skapar virtuell miljö..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installerar verktyg..." -ForegroundColor Yellow
& .\venv\Scripts\pip.exe install pyinstaller svtplay-dl

if (Test-Path "venv\Scripts\svtplay-dl.exe") {
    Copy-Item "venv\Scripts\svtplay-dl.exe" -Destination "bin\svtplay-dl.exe" -Force
} else {
    Write-Error "Svtplay-dl saknas."
    exit 1
}

# --- 2. YT-DLP ---
if (-not (Test-Path "bin\yt-dlp.exe")) {
    Write-Host "Laddar ner yt-dlp.exe..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile "bin\yt-dlp.exe" -UserAgent "QuickTubeBuilder/1.0"
    } catch {
        Write-Error "Kunde inte ladda ner yt-dlp."
        exit 1
    }
}

# --- 3. GUM ---
$gumVersion = "0.14.5"
$gumZip = "gum.zip"
if (-not (Test-Path "bin\gum.exe")) {
    Write-Host "Laddar ner gum..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://github.com/charmbracelet/gum/releases/download/v$gumVersion/gum_${gumVersion}_Windows_x86_64.zip" -OutFile $gumZip -UserAgent "QuickTubeBuilder/1.0"
        Expand-Archive -Path $gumZip -DestinationPath "gum_temp" -Force
        Move-Item -Path "gum_temp\gum_${gumVersion}_Windows_x86_64\gum.exe" -Destination "bin\gum.exe" -Force
    } catch {
        Write-Error "Kunde inte hämta gum."
        exit 1
    } finally {
        if (Test-Path $gumZip) { Remove-Item $gumZip }
        if (Test-Path "gum_temp") { Remove-Item "gum_temp" -Recurse -Force }
    }
}

# --- 4. BYGG ---
Write-Host "Kör PyInstaller..." -ForegroundColor Cyan
& .\venv\Scripts\pyinstaller.exe --onefile --clean --noconfirm `
    --add-binary "bin\gum.exe;bin" `
    --add-binary "bin\yt-dlp.exe;bin" `
    --add-binary "bin\svtplay-dl.exe;bin" `
    --name "quicktube" `
    quicktube.py

if (Test-Path "dist\quicktube.exe") {
    Write-Host ""
    Write-Host "✅ KLART! Filen finns i: $(Get-Location)\dist\quicktube.exe" -ForegroundColor Green
} else {
    Write-Host "❌ Bygget misslyckades." -ForegroundColor Red
}
Pause