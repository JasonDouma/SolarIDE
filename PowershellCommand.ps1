param (
    [string]$Command
)

$Command = $Command -replace '&&', ';'

if ($Command -match '^\s*([^\s|;]+)') {
    $cmdName = $Matches[1]
} else {
    Write-Error "Invalid or empty command format."
    exit 1
}

if (-not (Get-Command $cmdName -ErrorAction SilentlyContinue)) {
    Write-Error "The command '$cmdName' is not recognized as a valid PowerShell command."
    exit 1
}

Invoke-Expression $Command
