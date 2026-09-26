# TokenJar Windows 1-Click PowerShell Installer
# Usage:
#   iwr -useb https://raw.githubusercontent.com/Farukes/TokenJar/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🍯 Installing TokenJar Native Engine for Windows..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Repo = "Farukes/TokenJar"
$InstallDir = "$env:USERPROFILE\.tokenjar\bin"
$ZipPath = "$env:TEMP\tokenjar-windows-x64.zip"
$ExePath = "$InstallDir\tokenjar.exe"

# 1. Create target installation directory
if (!(Test-Path -Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 2. Get latest release download URL
try {
    $ReleaseApi = "https://api.github.com/repos/$Repo/releases/latest"
    $Release = Invoke-RestMethod -Uri $ReleaseApi -Headers @{ "User-Agent" = "TokenJar-Installer" }
    $Asset = $Release.assets | Where-Object { $_.name -like "*windows-x64.zip" } | Select-Object -First 1
    if ($Asset) {
        $DownloadUrl = $Asset.browser_download_url
    } else {
        $DownloadUrl = "https://github.com/$Repo/releases/latest/download/tokenjar-windows-x64.zip"
    }
} catch {
    $DownloadUrl = "https://github.com/$Repo/releases/latest/download/tokenjar-windows-x64.zip"
}

Write-Host "📥 Downloading TokenJar binary from $DownloadUrl..." -ForegroundColor Green
Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -UseBasicParsing

# 3. Extract executable
Write-Host "📦 Extracting into $InstallDir..." -ForegroundColor Green
Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
Remove-Item -Path $ZipPath -Force -ErrorAction SilentlyContinue

# 4. Add to User PATH if not present
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$InstallDir*") {
    Write-Host "🔗 Adding $InstallDir to User PATH environment variable..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$InstallDir;$UserPath", "User")
    $env:PATH = "$InstallDir;$env:PATH"
}

Write-Host "`n✨ TokenJar has been successfully installed!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if (Test-Path -Path $ExePath) {
    Write-Host "🔌 Auto-configuring MCP server across detected AI assistants..." -ForegroundColor Green
    & $ExePath on --global
    & $ExePath status
} else {
    Write-Host "Please restart your terminal to start using 'tokenjar'." -ForegroundColor Yellow
}
