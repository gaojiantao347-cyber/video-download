# video-download

一个本地桌面端视频下载工具，目标是用最小闭环完成公开视频链接下载：粘贴分享链接，创建下载任务，展示进度，保存视频到本地。

当前项目不做爬虫平台、不做后台系统，也不提供私密、付费、DRM、验证码或登录权限绕过能力。

## 核心能力

- 单个公开视频链接下载
- 支持抖音、快手公开视频链接识别
- 通过 `yt-dlp` 处理平台解析、短链跳转和视频下载
- 展示任务状态、下载进度、错误信息
- 下载完成后打开文件或打开所在目录
- 去水印作为 best-effort 下载偏好；不可用时可按配置降级普通下载

## 技术栈

| 模块 | 技术 | 职责 |
|---|---|---|
| 桌面端 UI | Vue 3、TypeScript、Element Plus、Pinia、Vue Query | 页面交互、任务展示、设置管理 |
| 桌面壳 | Tauri 2、Rust | `engine_rpc` facade、sidecar 启动、任务状态、文件路径校验 |
| 下载引擎 | Python 3.11+、yt-dlp、Playwright | 公开视频解析、下载、进度事件、错误映射 |
| 协议契约 | JSON Schema、JSON-RPC 文档 | 前端、Rust、Python 的接口边界 |
| 打包 | PyInstaller、Tauri CLI | 构建 `vd-engine.exe` 并打包桌面应用 |

## 目录结构

```text
video-download/
├── apps/
│   └── desktop-ui/              # Vue + Tauri 桌面端工程
│       ├── src/                 # 前端源码
│       └── src-tauri/           # Rust 主进程、RPC facade、Tauri 配置
├── engine-python/               # Python 下载引擎
│   ├── src/video_download_engine/
│   └── tests/
├── contracts/                   # RPC、DTO、错误码和 JSON Schema
├── docs/                        # 产品和技术文档
└── scripts/                     # 构建、打包、sidecar 复制脚本
```

## 工作流程

```text
用户输入公开视频链接
  ↓
Vue 通过 Tauri invoke('engine_rpc') 发送 JSON-RPC 请求
  ↓
Rust 创建任务并启动 Python vd-engine sidecar
  ↓
Python 调用 yt-dlp 下载并输出 JSON 进度事件
  ↓
Rust 更新任务状态
  ↓
Vue 展示下载进度、结果和文件操作入口
```

## 开发环境

除特别说明外，以下命令默认从项目根目录执行。

建议环境：

- Node.js + npm
- Rust + Tauri 依赖环境
- Python 3.11+
- Windows 环境优先使用 PowerShell 脚本

安装桌面端依赖：

```powershell
cd apps/desktop-ui
npm ci
```

安装 Python 下载引擎依赖：

```powershell
cd engine-python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,build]"
```

## 常用命令

前端检查和构建：

```powershell
cd apps/desktop-ui
npm run typecheck
npm run lint
npm run build
```

运行 Python 引擎测试：

```powershell
cd engine-python
.\.venv\Scripts\python.exe -m pytest
```

本地测试下载引擎：

```powershell
cd engine-python
.\.venv\Scripts\vd-engine.exe download --url "<公开视频链接>" --output-dir "D:\Videos"
```

打包桌面应用：

```powershell
.\scripts\package-desktop.ps1
```

该脚本会先构建 Python sidecar，再执行 Tauri 桌面端打包。

## 功能边界

MVP 支持：

- 单链接下载
- 抖音、快手公开视频链接
- 下载进度展示
- 下载成功后打开文件或所在目录
- 基础错误提示
- 当前进程内任务状态

MVP 不支持：

- 批量下载
- 用户系统
- 后台管理系统
- 跨重启历史记录
- 私密、付费、DRM 视频下载
- Cookie/Token 权限绕过
- 反风控、验证码绕过
- 视频画面级水印修复

## 协作约定

- 协议变更先改 `contracts/`，再同步 Rust、Python 和前端类型。
- `docs/` 记录产品和技术方案，不放运行时数据。
- `scripts/` 只放构建和打包脚本，不写业务逻辑。
- Python 下载核心只负责下载相关能力，平台解析优先交给 `yt-dlp`。

## 相关文档

- `docs/product/前端功能文档MVP.md`
- `docs/product/后端功能文档MVP.md`
- `docs/tech/项目目录结构规划.md`
- `docs/tech/后端架构迁移计划-Python-yt-dlp.md`
