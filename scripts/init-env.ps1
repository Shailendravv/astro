# Creates a local .env from .env.example with a random database password.
# Safe to run more than once: it never overwrites an existing .env.
# Model settings (RUNTIME_MODEL_ID, GROQ_API_KEY, judge) stay empty: AI features remain disabled until
# the owner fills them in (docs/decisions.md D-012, D-030).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$example = Join-Path $root ".env.example"
$target = Join-Path $root ".env"

if (Test-Path -LiteralPath $target) {
    Write-Host ".env already exists. Nothing changed."
    exit 0
}

# 32 random characters from a URL-safe alphabet (no characters that need quoting in a database URL).
$alphabet = (48..57) + (65..90) + (97..122) | ForEach-Object { [char]$_ }
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$password = -join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Count] })

$lines = Get-Content -LiteralPath $example | ForEach-Object {
    if ($_ -match '^POSTGRES_PASSWORD=') { "POSTGRES_PASSWORD=$password" } else { $_ }
}
# LF line endings, UTF-8 without BOM (the file is read inside Linux containers).
[System.IO.File]::WriteAllText($target, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Created .env with a random database password. Keep this file private; never commit it."
