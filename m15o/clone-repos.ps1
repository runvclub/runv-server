#Requires -Version 5.1
<#
.SYNOPSIS
    Clona todos os repositorios m15o listados em links_srht_m15o.txt na raiz do projeto.

.DESCRIPTION
    Le as secoes 2a, 2b e 3 de links_srht_m15o.txt e clona cada repositorio Git ou
    Mercurial em uma pasta com o nome do projeto na raiz do projeto.

.PARAMETER DryRun
    Apenas lista o que seria clonado, sem executar.

.NOTES
    Pre-requisitos: git (obrigatorio), hg/Mercurial (obrigatorio para repos hg.sr.ht)
#>
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot
$ListFile = Join-Path $ScriptDir "links_srht_m15o.txt"

function Write-Status {
    param([string]$Level, [string]$Name, [string]$Message = "")
    $suffix = if ($Message) { " - $Message" } else { "" }
    Write-Host "[$Level] $Name$suffix"
}

function Get-ReposFromList {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Arquivo nao encontrado: $Path"
    }

    $repos = @()
    $pattern = 'https://(git|hg)\.sr\.ht/~m15o/([^/\s#"$]+)'
    $inRepoSection = $false

    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        if ($line -match '^\s*2a\)|^\s*2b\)|^\s*3\)') {
            $inRepoSection = $true
            continue
        }
        if ($line -match '^\s*4\)') {
            break
        }
        if (-not $inRepoSection) { continue }
        if ($line -notmatch $pattern) { continue }

        $type = $Matches[1]
        $name = $Matches[2]
        if ($name -match '\.tar\.gz$') { continue }

        $repos += [PSCustomObject]@{
            Type = $type
            Name = $name
            Url  = "https://$type.sr.ht/~m15o/$name"
        }
    }

    # Deduplicar mantendo ordem de aparicao
    $seen = @{}
    $unique = @()
    foreach ($repo in $repos) {
        $key = "$($repo.Type)/$($repo.Name)"
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            $unique += $repo
        }
    }

    return $unique
}

function Test-RepoExists {
    param([string]$Dir)

    if (-not (Test-Path $Dir)) { return $false }
    return (Test-Path (Join-Path $Dir ".git")) -or (Test-Path (Join-Path $Dir ".hg"))
}

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# --- main ---
Write-Host "=== clone-repos.ps1 ==="
Write-Host "Diretorio: $ScriptDir"
Write-Host "Lista: $ListFile"
if ($DryRun) { Write-Host "Modo: DRY-RUN" }
Write-Host ""

$repos = Get-ReposFromList -Path $ListFile
Write-Host "Repositorios encontrados: $($repos.Count)"
Write-Host ""

if ($repos.Count -eq 0) {
    Write-Error "Nenhum repositorio encontrado em $ListFile"
    exit 1
}

$hasGit = Test-CommandExists "git"
$hasHg = Test-CommandExists "hg"
$needsHg = ($repos | Where-Object { $_.Type -eq "hg" }).Count -gt 0

if (-not $DryRun) {
    if (-not $hasGit) {
        Write-Error "git nao encontrado no PATH. Instale Git antes de continuar."
        exit 1
    }
    if ($needsHg -and -not $hasHg) {
        Write-Error "hg (Mercurial) nao encontrado no PATH. Instale Mercurial antes de continuar."
        exit 1
    }
}

$stats = @{ OK = 0; SKIP = 0; FAIL = 0 }
$failed = @()

foreach ($repo in $repos) {
    $targetDir = Join-Path $ScriptDir $repo.Name

    if (Test-RepoExists -Dir $targetDir) {
        Write-Status "SKIP" $repo.Name "pasta ja existe"
        $stats.SKIP++
        continue
    }

    if (Test-Path $targetDir) {
        Write-Status "SKIP" $repo.Name "pasta existe mas sem .git/.hg - nao sobrescrevendo"
        $stats.SKIP++
        continue
    }

    if ($DryRun) {
        Write-Status "DRY-RUN" $repo.Name "$($repo.Type) clone $($repo.Url)"
        $stats.OK++
        continue
    }

    Write-Status "CLONE" $repo.Name "$($repo.Type) $($repo.Url)"

    if ($repo.Type -eq "git") {
        & git clone $repo.Url $targetDir 2>&1 | Out-Host
        $exitCode = $LASTEXITCODE
    }
    else {
        & hg clone $repo.Url $targetDir 2>&1 | Out-Host
        $exitCode = $LASTEXITCODE
    }

    if ($exitCode -eq 0 -and (Test-RepoExists -Dir $targetDir)) {
        Write-Status "OK" $repo.Name
        $stats.OK++
    }
    else {
        Write-Status "FAIL" $repo.Name "exit code $exitCode"
        $stats.FAIL++
        $failed += $repo.Name
        if (Test-Path $targetDir) {
            Remove-Item -Path $targetDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "=== Resumo ==="
Write-Host "Total: $($repos.Count) | OK: $($stats.OK) | SKIP: $($stats.SKIP) | FAIL: $($stats.FAIL)"

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Falharam:"
    foreach ($name in $failed) {
        Write-Host "  - $name"
    }
    exit 1
}

exit 0
