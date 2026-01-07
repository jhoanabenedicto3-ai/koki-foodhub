<#
PowerShell helper to export local Django data and import into a remote
Postgres database (Render). Usage:

1. Activate your virtualenv: & .\.venv\Scripts\Activate.ps1
2. Run this script: .\scripts\import_to_render.ps1

The script will:
- create a `data.json` fixture using `dumpdata` (excludes contenttypes and
  auth.permission)
- prompt for (or read from env) a `DATABASE_URL` for the target Render DB
- run migrations against the target database and load the fixture

Notes:
- This imports Django model data only. Media files under `media/` must be
  uploaded separately (S3 or Render persistent volume).
- For large databases or complex custom fields, consider using a SQL dump
  + `pg_restore` approach instead.
#>

Set-StrictMode -Version Latest
Push-Location (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent) | Out-Null
Pop-Location | Out-Null

Write-Host "Creating Django fixture (data.json). This may take a while..." -ForegroundColor Cyan
& python manage.py dumpdata --natural-primary --natural-foreign --exclude auth.permission --exclude contenttypes --indent 2 > data.json

if ($LASTEXITCODE -ne 0) {
    Write-Error "dumpdata failed. Aborting. Check your local DB and try again."
    exit 1
}

$dburl = $env:DATABASE_URL
if (-not $dburl) {
    $dburl = Read-Host "Enter the target Render DATABASE_URL (format: postgres://user:pass@host:port/dbname)"
}

if (-not $dburl) {
    Write-Error "No DATABASE_URL provided. Aborting."
    exit 1
}

Write-Host "Using target DATABASE_URL: (hidden)" -ForegroundColor Yellow

# Export current env so manage.py uses the target DB for the migrate/loaddata commands
$originalDb = $env:DATABASE_URL
$env:DATABASE_URL = $dburl

Write-Host "Running migrations on target database..." -ForegroundColor Cyan
& python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) {
    Write-Error "migrate failed against target DB. Restoring original env and aborting."
    $env:DATABASE_URL = $originalDb
    exit 1
}

Write-Host "Loading fixture into target database..." -ForegroundColor Cyan
& python manage.py loaddata data.json
if ($LASTEXITCODE -ne 0) {
    Write-Error "loaddata failed. Restoring original env and aborting."
    $env:DATABASE_URL = $originalDb
    exit 1
}

# restore original env var
$env:DATABASE_URL = $originalDb

Write-Host "Import complete.\n- Data fixture: data.json\n- Remember to upload media files (media/) separately." -ForegroundColor Green
