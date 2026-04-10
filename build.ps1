#Requires -Version 5.1
<#
.SYNOPSIS
  Builds the service-common sdist and wheel (PEP 517) in dist\.

.PARAMETER Version
  Expected package version string; must match [project].version in pyproject.toml
  and the produced dist\ filenames (default: 0.1.0).

.EXAMPLE
  .\build.ps1
.EXAMPLE
  .\build.ps1 -Version 0.2.0
#>
param(
    [string] $Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$PackageRoot = $PSScriptRoot

Set-Location -LiteralPath $PackageRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'python not found in PATH. Install Python 3.11+ or activate your venv first.'
}

python -m pip install --upgrade pip build
python -m build

$dist = Join-Path $PackageRoot 'dist'
$wheel = Get-ChildItem -LiteralPath $dist -Filter "service_common-$Version-*.whl" -ErrorAction SilentlyContinue |
    Select-Object -First 1
$sdist = Join-Path $dist "service_common-$Version.tar.gz"

if (-not $wheel) {
    throw "Expected wheel matching service_common-$Version-*.whl not found under dist\."
}
if (-not (Test-Path -LiteralPath $sdist)) {
    throw "Expected sdist not found: $sdist"
}

Write-Host "Built: $($wheel.FullName)"
Write-Host "Built: $sdist"
