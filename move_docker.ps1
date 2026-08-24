Write-Host "Closing Docker Desktop if it is running..." -ForegroundColor Yellow
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "DockerEngine" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Write-Host "`nShutting down WSL..."
wsl --shutdown

$targetDir = "D:\DockerData"
$targetDataDir = "$targetDir\data"
$tarFile = "$targetDir\docker-desktop-data.tar"

Write-Host "Creating directories on D drive..."
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }
if (!(Test-Path $targetDataDir)) { New-Item -ItemType Directory -Path $targetDataDir | Out-Null }

Write-Host "Exporting current Docker data to $tarFile (This may take a few minutes)..."
wsl --export docker-desktop-data $tarFile

Write-Host "Unregistering old Docker data from C drive..."
wsl --unregister docker-desktop-data

Write-Host "Importing Docker data to D drive..."
wsl --import docker-desktop-data $targetDataDir $tarFile --version 2

Write-Host "Cleaning up backup tar file..."
Remove-Item $tarFile

Write-Host "Done! Docker data has been successfully moved to D drive." -ForegroundColor Green
Write-Host "You can now open Docker Desktop again from your Start menu."
