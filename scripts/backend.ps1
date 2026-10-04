# Run backend Python commands with the project's ignored local configuration.
# Example: ./scripts/backend.ps1 -m pytest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$configuration = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $configuration) {
    foreach ($line in Get-Content -LiteralPath $configuration) {
        if ($line -match '^([A-Z][A-Z0-9_]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
        }
    }
}
Push-Location (Join-Path $projectRoot 'backend')
try {
    & (Join-Path $projectRoot '.venv/Scripts/python.exe') @args
    $commandExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $commandExitCode
