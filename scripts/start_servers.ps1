# Quick launcher for backend (uvicorn) and frontend (Next.js) on Windows.
# Uses short paths to avoid spaces in "Program Files".

param(
    [switch]$NoFrontend
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

$logsDir = Join-Path $repoRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

$backendOut = Join-Path $logsDir "backend-uvicorn.out.log"
$backendErr = Join-Path $logsDir "backend-uvicorn.err.log"
$frontendOut = Join-Path $logsDir "frontend-dev.out.log"
$frontendErr = Join-Path $logsDir "frontend-dev.err.log"

# Backend
$backendArgs = @(
    "-m", "uvicorn", "backend.main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--reload"
)
$backend = Start-Process -FilePath "python" `
    -ArgumentList $backendArgs `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendErr `
    -PassThru

# Frontend (skip with -NoFrontend)
if (-not $NoFrontend) {
    $nodeExe = "C:\Progra~1\nodejs\node.exe"
    $npmCli = "C:\Progra~1\nodejs\node_modules\npm\bin\npm-cli.js"

    if (-not (Test-Path $nodeExe) -or -not (Test-Path $npmCli)) {
        Write-Warning "Node or npm CLI not found at expected paths. Frontend not started."
    }
    else {
        $frontendArgs = @(
            $npmCli,
            "--prefix", (Join-Path $repoRoot "frontend"),
            "run", "dev"
        )
        $frontend = Start-Process -FilePath $nodeExe `
            -ArgumentList $frontendArgs `
            -WorkingDirectory (Join-Path $repoRoot "frontend") `
            -RedirectStandardOutput $frontendOut `
            -RedirectStandardError $frontendErr `
            -PassThru
    }
}

Write-Host "Backend PID : $($backend.Id) | Logs: $backendOut / $backendErr"
if ($frontend) {
    Write-Host "Frontend PID: $($frontend.Id) | Logs: $frontendOut / $frontendErr"
}
elseif (-not $NoFrontend) {
    Write-Host "Frontend not started. See warnings above."
}

Write-Host "Check: http://localhost:8000 and http://localhost:3000"
Write-Host "Stop:  Stop-Process -Id $($backend.Id)$(if ($frontend) { \", $($frontend.Id)\" })"
