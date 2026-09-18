# 开发环境一键启动：geochat 后端容器 + yuxi 前端 dev server + 门户 dev server。
#
# 拓扑（务必保持一致，详见 apps/web/vite.config.ts 与 services/yuxi/docker/nginx/default.conf）：
#   门户(深地智学)   http://127.0.0.1:5174   ← apps/web vite dev（/geochat 代理不剥前缀）
#   GeoChat          http://127.0.0.1:5174/geochat/…  ← 同一入口，代理到 5177
#   yuxi dev server  http://127.0.0.1:5177   ← 必须 VITE_BASE_PATH=/geochat/（与容器构建一致）
#   GeoChat API      http://127.0.0.1:5050   ← docker compose（geochat-runtime 项目）
#
# 用法：powershell -ExecutionPolicy Bypass -File scripts\dev-up.ps1 [-Down] [-Status]

param(
  [switch]$Down,
  [switch]$Status
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$geoChatRoot = Join-Path $repoRoot 'services\yuxi'
$geoChatWebRoot = Join-Path $geoChatRoot 'web'
$portalWebRoot = Join-Path $repoRoot 'apps\web'

$composeArgs = @('--project-name', 'geochat-runtime', '--project-directory', $geoChatRoot)

function Get-ListeningPortPid {
  param([int]$Port)
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($conn) { return $conn.OwningProcess }
  return $null
}

function Stop-DevServerOnPort {
  param([int]$Port, [string]$Name)
  $pid = Get-ListeningPortPid -Port $Port
  if ($pid) {
    Write-Host "停止 $Name (端口 $Port, PID $pid)"
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
  }
}

if ($Down) {
  Stop-DevServerOnPort -Port 5174 -Name '门户 dev server'
  Stop-DevServerOnPort -Port 5177 -Name 'GeoChat dev server'
  Write-Host '停止 geochat-runtime 容器栈…'
  & docker compose @composeArgs stop
  exit 0
}

if ($Status) {
  & docker compose @composeArgs ps
  foreach ($port in 5174, 5177) {
    $pid = Get-ListeningPortPid -Port $port
    if ($pid) { Write-Host "端口 $port : PID $pid" } else { Write-Host "端口 $port : 空闲" }
  }
  exit 0
}

# 1) 后端容器栈（api/worker/postgres/redis/minio/sandbox-provisioner）。
#    web 容器在 dev 下仍排除：镜像 0.7.3 起已修复 /geochat 适配（生产构建验证通过），
#    但 5173 可能被残留的 vite dev server 占用（端口竞争不确定），dev 统一走 5174/5177。
#    镜像统一走 daocloud 镜像源（与 start-platform.ps1 一致），否则 docker.io 不可达时拉取失败。
$env:DOCKER_IMAGE_PREFIX = 'docker.m.daocloud.io/library/'
$env:GHCR_IMAGE_PREFIX = 'ghcr.m.daocloud.io/'
$env:YUXI_POSTGRES_IMAGE = 'docker.m.daocloud.io/library/postgres:16'
$env:YUXI_REDIS_IMAGE = 'docker.m.daocloud.io/library/redis:7.4.10-alpine'
$env:YUXI_MINIO_IMAGE = 'docker.m.daocloud.io/minio/minio:RELEASE.2023-03-20T20-16-18Z'
Write-Host '启动 GeoChat 后端容器栈（不含 web 容器）…'
& docker compose @composeArgs up -d --scale web=0
if ($LASTEXITCODE -ne 0) { throw 'docker compose up 失败' }

# 2) yuxi 前端 dev server（5177）。base 必须是 /geochat/，与容器构建参数一致。
if (Get-ListeningPortPid -Port 5177) {
  Write-Host 'GeoChat dev server 已在 5177 运行，跳过'
} else {
  Write-Host '启动 GeoChat dev server (5177)…'
  Start-Process -FilePath 'cmd.exe' -ArgumentList @(
    '/k', "cd /d `"$geoChatWebRoot`" && set VITE_BASE_PATH=/geochat/&& set VITE_API_BASE_PATH=/geochat&& npm run dev -- --port 5177 --strictPort"
  ) | Out-Null
}

# 3) 门户 dev server（5174）。
if (Get-ListeningPortPid -Port 5174) {
  Write-Host '门户 dev server 已在 5174 运行，跳过'
} else {
  Write-Host '启动门户 dev server (5174)…'
  Start-Process -FilePath 'cmd.exe' -ArgumentList @(
    '/k', "cd /d `"$portalWebRoot`" && npm run dev -- --port 5174 --strictPort"
  ) | Out-Null
}

# 4) 健康检查
Write-Host '等待服务就绪…'
$deadline = (Get-Date).AddSeconds(120)
do {
  Start-Sleep -Seconds 3
  $ok = $true
  try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:5174/geochat/api/system/health' -TimeoutSec 5
    $ok = $health.status -eq 'ok'
  } catch { $ok = $false }
} while (-not $ok -and (Get-Date) -lt $deadline)

if ($ok) {
  Write-Host ''
  Write-Host '全部就绪：'
  Write-Host '  门户(深地智学):  http://127.0.0.1:5174'
  Write-Host '  智能应用:        http://127.0.0.1:5174/capability/geology-design'
  Write-Host '  GeoChat 登录:    http://127.0.0.1:5174/geochat/login'
} else {
  Write-Warning '服务未在时限内就绪，请检查上方两个窗口的输出'
}
