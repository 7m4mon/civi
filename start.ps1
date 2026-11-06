param([switch]$ResetPassword)

$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$config = Join-Path $PSScriptRoot 'config.toml'
$passwordFile = Join-Path $PSScriptRoot '.civi-password.xml'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv\Scripts\python.exe. Create the virtual environment and install CIVI first.'
}
if (-not (Test-Path -LiteralPath $config)) {
    throw 'Missing config.toml. Copy config.example.toml and configure it first.'
}

Push-Location -LiteralPath $PSScriptRoot
try {
    $passwordEnv = & $python -c "import tomllib; print(tomllib.load(open('config.toml', 'rb'))['password_env'])"
    if ($LASTEXITCODE -ne 0) { throw 'Could not read config.toml.' }
    if ($passwordEnv -notmatch '^[a-zA-Z_][a-zA-Z0-9_]*$') { throw 'Invalid password_env in config.toml.' }

    if ($ResetPassword -or -not (Test-Path -LiteralPath $passwordFile)) {
        do {
            $securePassword = Read-Host 'CIVI Web password (at least 12 characters)' -AsSecureString
            if ($securePassword.Length -lt 12) { Write-Host 'The password must contain at least 12 characters.' }
        } while ($securePassword.Length -lt 12)
        $credential = New-Object System.Management.Automation.PSCredential('admin', $securePassword)
        # On Windows, Export-Clixml protects the credential with user-scoped DPAPI.
        $credential | Export-Clixml -LiteralPath $passwordFile
        Write-Host 'Saved the encrypted password for this Windows account on this computer.'
    } else {
        try {
            $credential = Import-Clixml -LiteralPath $passwordFile
            if ($credential -isnot [System.Management.Automation.PSCredential]) { throw 'Invalid credential file.' }
            $null = $credential.GetNetworkCredential().Password
        } catch {
            throw 'Cannot read the saved password. Run start.cmd -ResetPassword to replace it.'
        }
    }

    $previousPassword = [Environment]::GetEnvironmentVariable($passwordEnv, 'Process')
    try {
        [Environment]::SetEnvironmentVariable($passwordEnv, $credential.GetNetworkCredential().Password, 'Process')
        Write-Host 'Starting CIVI. Press Ctrl+C to stop.'
        & $python -m civi --config config.toml
        if ($LASTEXITCODE -ne 0) { throw "CIVI exited with code $LASTEXITCODE." }
    } finally {
        [Environment]::SetEnvironmentVariable($passwordEnv, $previousPassword, 'Process')
        $credential = $null
        $securePassword = $null
    }
} finally {
    Pop-Location
}
