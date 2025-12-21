# build_windows.ps1
# Byggscript för QuickTube på Windows 10/11
# Kör detta script i PowerShell som administratör (eller se till att du har rättigheter att skriva i mappen)

# Tvinga TLS 1.2 för säkrare nedladdningar
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Bygger QuickTube för Windows..." -ForegroundColor Cyan

# --- CLEANUP ---
# Ta bort venv om den är trasig
if (Test-Path "venv") {
    if (-not (Test-Path "venv\Scripts\pip.exe")) {
        Write-Host "Rensar gammal/ogiltig venv..." -ForegroundColor Yellow
        Remove-Item "venv" -Recurse -Force
    }
}
if (-not (Test-Path "bin")) { New-Item -ItemType Directory -Force -Path "bin" | Out-Null }

# --- 1. SÄTT UPP PYTHON & HÄMTA SVTPLAY-DL VIA PIP ---
if (-not (Test-Path "venv")) {
    Write-Host "Skapar virtuell miljö..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installerar beroenden och verktyg..." -ForegroundColor Yellow
# Vi installerar svtplay-dl via pip för att få en korrekt .exe genererad av pip i venv/Scripts
& .\venv\Scripts\pip.exe install pyinstaller svtplay-dl

# Kopiera den genererade svtplay-dl.exe från venv till bin
if (Test-Path "venv\Scripts\svtplay-dl.exe") {
    Write-Host "Hittade svtplay-dl via pip, kopierar till bin/..." -ForegroundColor Green
    Copy-Item "venv\Scripts\svtplay-dl.exe" -Destination "bin\svtplay-dl.exe" -Force
} else {
    Write-Error "Kunde inte hitta svtplay-dl.exe i venv/Scripts efter installation."
    exit 1
}

# --- 2. HÄMTA YT-DLP ---
Write-Host "Laddar ner yt-dlp.exe..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile "bin\yt-dlp.exe" -UserAgent "QuickTubeBuilder/1.0"
} catch {
    Write-Error "Kunde inte ladda ner yt-dlp. Kontrollera internet."
    exit 1
}

# --- 3. HÄMTA GUM ---
$gumVersion = "0.14.5"
$gumUrl = "https://github.com/charmbracelet/gum/releases/download/v$gumVersion/gum_${gumVersion}_Windows_x86_64.zip"
$gumZip = "gum.zip"

if (-not (Test-Path "bin\gum.exe")) {
    Write-Host "Laddar ner gum..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $gumUrl -OutFile $gumZip -UserAgent "QuickTubeBuilder/1.0"
        Expand-Archive -Path $gumZip -DestinationPath "gum_temp" -Force
        
        $extractedGumPath = "gum_temp\gum_${gumVersion}_Windows_x86_64\gum.exe"
        if (Test-Path $extractedGumPath) {
            Move-Item -Path $extractedGumPath -Destination "bin\gum.exe" -Force
        } else {
            Write-Error "Hittade inte gum.exe i zip-filen."
            exit 1
        }
    } catch {
        Write-Error "Misslyckades med gum-nedladdning."
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
    Write-Host "✅ SUCCÉ! Filen finns här:" -ForegroundColor Green
    Write-Host "   $(Get-Location)\dist\quicktube.exe" -ForegroundColor White
} else {
    Write-Host "❌ Bygget misslyckades." -ForegroundColor Red
}

Pause
