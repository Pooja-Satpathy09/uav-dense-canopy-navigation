param(
    [string]$Destination = (Join-Path (Split-Path $PSScriptRoot -Parent) 'uav-dense-canopy-navigation-git')
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Destination) { throw 'Destination already exists. Choose a new destination.' }
$packageRoot = $PSScriptRoot
$repoUrl = 'https://github.com/Pooja-Satpathy09/uav-dense-canopy-navigation.git'
git clone --no-recurse-submodules $repoUrl $Destination
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed.' }
$checkoutRoot = (Resolve-Path -LiteralPath $Destination).Path
git -C $checkoutRoot switch -c codex/ten-metric-benchmark a09299e5525b8098d378d402e8ef3f20ca290e26
if ($LASTEXITCODE -ne 0) { throw 'Creating the pinned branch failed.' }
git -C $checkoutRoot submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { throw 'Submodule initialization failed.' }
foreach ($relative in Get-Content -LiteralPath (Join-Path $packageRoot 'ADDED_FILES.txt')) {
    if ([string]::IsNullOrWhiteSpace($relative)) { continue }
    if ([System.IO.Path]::IsPathRooted($relative) -or ($relative -split '[/\\]') -contains '..') {
        throw "Invalid package path: $relative"
    }
    $sourceFile = Join-Path $packageRoot $relative
    $targetFile = Join-Path $checkoutRoot $relative
    if (Test-Path -LiteralPath $targetFile) { throw "Refusing to overwrite: $targetFile" }
    $targetParent = Split-Path $targetFile -Parent
    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile -Destination $targetFile
}
Write-Host "Project ready at: $checkoutRoot"
git -C $checkoutRoot status --short
