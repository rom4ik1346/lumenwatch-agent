$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Run:"
    Write-Host "  python -m venv .venv"
    Write-Host '  .\.venv\Scripts\python.exe -m pip install -e ".[dev]"'
    exit 1
}

$arguments = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8020", "--reload")
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    $arguments += @("--env-file", $envFile)
}

& $python @arguments

