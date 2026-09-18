param(
  [switch]$Build,
  [switch]$Down,
  [switch]$Restart,
  [switch]$Deploy,
  [switch]$Status,
  [switch]$Logs,
  [switch]$Health,
  [switch]$KnowledgeServices,
  [string]$ImageRegistryMirror = 'docker.m.daocloud.io',
  [ValidateRange(30, 900)]
  [int]$TimeoutSeconds = 360
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$geoChatRoot = Join-Path $repoRoot 'services\yuxi'
$portalCompose = Join-Path $repoRoot 'infra\compose\docker-compose.yml'
$portalEnvironment = Join-Path $repoRoot '.env'
$portalEnvironmentExample = Join-Path $repoRoot '.env.example'
$geoChatEnvironment = Join-Path $geoChatRoot '.env'
$geoChatEnvironmentTemplate = Join-Path $geoChatRoot '.env.template'
$geoChatComposeArgs = @('--project-name', 'geochat-runtime', '--project-directory', $geoChatRoot)
if ($KnowledgeServices) {
  $geoChatComposeArgs += @('--profile', 'knowledge')
}
$portalComposeArgs = @('--project-name', 'deep-geology', '--project-directory', $repoRoot, '-f', $portalCompose)

function Set-DefaultEnvironmentValue {
  param(
    [string]$Name,
    [string]$Value
  )

  if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($Name, 'Process'))) {
    [Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
  }
}

function New-RandomHex([int]$ByteCount) {
  $bytes = [byte[]]::new($ByteCount)
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
    return -join ($bytes | ForEach-Object { $_.ToString('x2') })
  } finally {
    $rng.Dispose()
  }
}

function Ensure-GeoChatEnvironment {
  if (-not (Test-Path -LiteralPath $geoChatEnvironment)) {
    Copy-Item -LiteralPath $geoChatEnvironmentTemplate -Destination $geoChatEnvironment
    Write-Host 'Created services/yuxi/.env with local security defaults.'
  }

  $content = Get-Content -LiteralPath $geoChatEnvironment -Raw
  $secrets = @{
    'JWT_SECRET_KEY' = New-RandomHex 32
    'API_KEY_DERIVATION_SECRET' = New-RandomHex 32
    'SANDBOX_PROVISIONER_TOKEN' = New-RandomHex 32
    'YUXI_INSTANCE_ID' = "instance-$(New-RandomHex 8)"
  }
  foreach ($name in $secrets.Keys) {
    $pattern = "(?m)^$([regex]::Escape($name))=.*$"
    if ($content -notmatch $pattern) {
      $content += "`n$name=$($secrets[$name])"
    } elseif ($content -match "(?m)^$([regex]::Escape($name))=\s*$") {
      $content = [regex]::Replace($content, $pattern, "$name=$($secrets[$name])", 1)
    }
  }
  Set-Content -LiteralPath $geoChatEnvironment -Value $content -Encoding UTF8
}

function Set-PlatformImageOverrides {
  param([string]$Mirror)

  if ([string]::IsNullOrWhiteSpace($Mirror)) {
    return
  }

  $base = $Mirror.TrimEnd('/')
  Set-DefaultEnvironmentValue -Name 'PORTAL_POSTGRES_IMAGE' -Value "$base/pgvector/pgvector:pg16"
  Set-DefaultEnvironmentValue -Name 'PORTAL_REDIS_IMAGE' -Value "$base/library/redis:7-alpine"
  Set-DefaultEnvironmentValue -Name 'PORTAL_MINIO_IMAGE' -Value "$base/minio/minio:RELEASE.2023-03-20T20-16-18Z"
  Set-DefaultEnvironmentValue -Name 'DOCKER_IMAGE_PREFIX' -Value "$base/library/"
  Set-DefaultEnvironmentValue -Name 'GHCR_IMAGE_PREFIX' -Value 'ghcr.m.daocloud.io/'
  Set-DefaultEnvironmentValue -Name 'YUXI_NEO4J_IMAGE' -Value "$base/library/neo4j:5.26.29"
  Set-DefaultEnvironmentValue -Name 'YUXI_MINIO_IMAGE' -Value "$base/minio/minio:RELEASE.2023-03-20T20-16-18Z"
  Set-DefaultEnvironmentValue -Name 'YUXI_MILVUS_IMAGE' -Value "$base/milvusdb/milvus:v2.5.6"
  Set-DefaultEnvironmentValue -Name 'YUXI_POSTGRES_IMAGE' -Value "$base/library/postgres:16"
  Set-DefaultEnvironmentValue -Name 'YUXI_REDIS_IMAGE' -Value "$base/library/redis:7.4.10-alpine"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw 'Docker Desktop and Docker Compose are required to run the platform.'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
  throw 'Docker CLI is installed, but the Docker Linux engine is not running. Start Docker Desktop, wait until it reports "Running", then rerun this command.'
}

Set-PlatformImageOverrides -Mirror $ImageRegistryMirror

function Invoke-PlatformCompose {
  param(
    [string[]]$ComposeArgs,
    [string[]]$CommandArgs
  )

  & docker compose @ComposeArgs @CommandArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose command failed: $($CommandArgs -join ' ')"
  }
}

function Show-PlatformStatus {
  Write-Host 'Portal services:'
  Invoke-PlatformCompose -ComposeArgs $portalComposeArgs -CommandArgs @('ps', '--all')
  Write-Host ''
  Write-Host 'GeoChat services:'
  Invoke-PlatformCompose -ComposeArgs $geoChatComposeArgs -CommandArgs @('ps', '--all')
}

function Wait-ForHttpService {
  param(
    [string]$Name,
    [string]$Uri,
    [int]$Timeout
  )

  $deadline = (Get-Date).AddSeconds($Timeout)
  $lastFailure = ''
  do {
    try {
      $response = Invoke-WebRequest -Uri $Uri -TimeoutSec 10 -UseBasicParsing
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
        Write-Host "$Name is ready: $Uri"
        return
      }
      $lastFailure = "HTTP $($response.StatusCode)"
    } catch {
      $lastFailure = $_.Exception.Message
    }
    Start-Sleep -Seconds 3
  } while ((Get-Date) -lt $deadline)

  throw "$Name did not become ready within $Timeout seconds: $lastFailure"
}

function Test-PlatformHealth {
  param([int]$Timeout)

  Wait-ForHttpService -Name 'Portal API' -Uri 'http://127.0.0.1:8000/readyz' -Timeout $Timeout
  Wait-ForHttpService -Name 'GeoChat API' -Uri 'http://127.0.0.1:5050/api/system/ready' -Timeout $Timeout
  Wait-ForHttpService -Name 'Portal web' -Uri 'http://127.0.0.1:8080/' -Timeout $Timeout
  Wait-ForHttpService -Name 'GeoChat gateway' -Uri 'http://127.0.0.1:8080/geochat/' -Timeout $Timeout
}

function Stop-Platform {
  Invoke-PlatformCompose -ComposeArgs $portalComposeArgs -CommandArgs @('down')
  Invoke-PlatformCompose -ComposeArgs $geoChatComposeArgs -CommandArgs @('down')
}

if ($Down) {
  Stop-Platform
  exit 0
}

if ($Status) {
  Show-PlatformStatus
  exit 0
}

if ($Logs) {
  Write-Host 'Portal logs:'
  Invoke-PlatformCompose -ComposeArgs $portalComposeArgs -CommandArgs @('logs', '--tail', '200')
  Write-Host ''
  Write-Host 'GeoChat logs:'
  Invoke-PlatformCompose -ComposeArgs $geoChatComposeArgs -CommandArgs @('logs', '--tail', '200')
  exit 0
}

if ($Health) {
  Test-PlatformHealth -Timeout $TimeoutSeconds
  exit 0
}

if ($Restart) {
  Stop-Platform
}

if (-not (Test-Path $portalEnvironment)) {
  Copy-Item -LiteralPath $portalEnvironmentExample -Destination $portalEnvironment
  Write-Host 'Created .env from .env.example. Update local passwords before production use.'
}

Ensure-GeoChatEnvironment

$upArgs = @('up', '-d')
if ($Build) {
  # Compose does not recreate a service merely because its stable image tag was rebuilt.
  # A unified platform build must also activate the image it produced.
  $upArgs += @('--build', '--force-recreate')
} elseif ($Deploy) {
  $upArgs += '--force-recreate'
}

Invoke-PlatformCompose -ComposeArgs $geoChatComposeArgs -CommandArgs $upArgs
Invoke-PlatformCompose -ComposeArgs $portalComposeArgs -CommandArgs $upArgs
Test-PlatformHealth -Timeout $TimeoutSeconds

Write-Host 'Platform: http://localhost:8080'
Write-Host 'GeoChat: http://localhost:8080/geochat/agent'
$lanAddresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
  Select-Object -ExpandProperty IPAddress -Unique
foreach ($lanAddress in $lanAddresses) {
  Write-Host "LAN: http://$lanAddress`:8080"
}
