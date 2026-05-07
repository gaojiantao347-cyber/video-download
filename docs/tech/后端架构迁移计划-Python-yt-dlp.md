# 后端架构决策：Python + yt-dlp 本地下载核心

## 1. 背景

当前项目目标是做一个本地桌面视频下载器，核心链路是：

```text
输入公开视频链接 → 解析与下载 → 保存到本地 → 展示任务状态
```

公开视频平台页面和接口变化快，手写页面解析维护成本高。当前架构统一复用 `yt-dlp` 的 extractor 和下载能力，项目自身专注桌面交互、任务状态、下载目录、错误展示和打包体验。

## 2. 核心结论

当前后端主链路固定为：

```text
Vue 前端
  ↓ Tauri invoke('engine_rpc') + JSON-RPC envelope
Tauri/Rust EngineProcessManager
  ↓ Python CLI 参数 + stdout JSON 事件
Python vd-engine
  ↓ yt-dlp
平台解析 + 视频下载 + 进度回传
```

## 3. 目标

| 目标 | 说明 |
|---|---|
| 优先跑通下载 | 先保证公开视频能下载，再扩展其他能力 |
| 降低平台解析维护成本 | 复用 `yt-dlp`，避免手写平台签名和接口逻辑 |
| 保留桌面端资产 | 继续使用 Vue + Tauri UI |
| 简化后端边界 | Python 引擎只做下载相关能力 |
| 支持后续打包 | `vd-engine(.exe)` 作为 Tauri sidecar 随应用发布 |

## 4. 非目标

| 非目标 | 原因 |
|---|---|
| 不继续手写平台解析器 | 维护成本高，容易失效 |
| 不先重建复杂任务系统 | MVP 阶段先验证下载能力 |
| 不承诺所有平台永久稳定 | 平台规则变化不可控，需依赖上游工具更新 |
| 不做绕过登录/权限的能力 | 只支持用户有权访问的公开视频或用户自己提供 Cookie 的场景 |

## 5. 推荐目录结构

```text
video-download/
├── apps/
│   └── desktop-ui/                 # Vue + Tauri 桌面端
├── engine-python/                  # Python 下载引擎
│   ├── pyproject.toml
│   ├── src/
│   │   └── video_download_engine/
│   │       ├── cli.py              # sidecar 入口
│   │       ├── downloader.py       # yt-dlp 封装
│   │       ├── protocol.py         # 请求/响应结构
│   │       ├── errors.py           # 错误映射
│   │       └── progress.py         # 进度事件转换
│   ├── tests/
│   └── dist/                       # PyInstaller 输出 vd-engine.exe
├── contracts/                      # 前端、Rust facade、Python 引擎的协议边界
├── docs/
└── scripts/                        # 构建和打包脚本
```

## 6. Python 下载引擎职责

| 模块 | 职责 |
|---|---|
| `cli.py` | 接收桌面端传入的参数，输出 JSON 事件 |
| `downloader.py` | 调用 `yt-dlp` 下载视频，监听进度 |
| `protocol.py` | 定义 `DownloadRequest`、`ProgressEvent`、`CompletedEvent`、`FailedEvent` |
| `errors.py` | 把 `yt-dlp` 异常映射成前端可理解的错误码 |
| `progress.py` | 将下载百分比、速度、ETA、文件名转换成统一事件 |

## 7. 最小协议设计

### 7.1 下载请求

```json
{
  "type": "download",
  "requestId": "uuid",
  "url": "https://v.douyin.com/example/",
  "outputDir": "D:/Videos",
  "removeWatermark": true,
  "allowFallback": true,
  "cookiesFile": null
}
```

### 7.2 进度事件

```json
{
  "type": "progress",
  "requestId": "uuid",
  "status": "downloading",
  "percent": 42.5,
  "speed": "1.2MiB/s",
  "eta": 18,
  "fileName": "video.mp4"
}
```

### 7.3 成功事件

```json
{
  "type": "completed",
  "requestId": "uuid",
  "filePath": "D:/Videos/video.mp4",
  "title": "视频标题"
}
```

### 7.4 失败事件

```json
{
  "type": "failed",
  "requestId": "uuid",
  "errorCode": "DOWNLOAD_FAILED",
  "message": "下载失败：平台解析失败或链接不可访问"
}
```

## 8. 当前实施状态

| 阶段 | 状态 | 输出 |
|---|---|---|
| Python 下载能力 | 已完成 | `engine-python` 提供 `vd-engine download` 命令 |
| Tauri 调用 sidecar | 已完成 | Rust 启动 Python 引擎并读取 stdout JSON 事件 |
| 桌面任务状态 | 已完成 | Rust 维护当前进程内 `DownloadTask` |
| 打包发布 | 已落地 | PyInstaller 输出 `vd-engine.exe`，Tauri build 前复制 sidecar |

## 9. 去水印策略

MVP 不承诺强制去水印。推荐策略：

| 策略 | 说明 |
|---|---|
| 默认优先下载最佳可用格式 | 交给 `yt-dlp` 选择 |
| `removeWatermark=true` | 作为偏好传入下载策略，不保证所有平台成功 |
| `allowFallback=true` | 无无水印资源时允许下载带水印版本 |
| 明确错误提示 | 不要把“无水印不可用”伪装成普通下载失败 |

## 10. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 平台风控 | 个别链接失败 | 支持清晰错误提示，必要时支持用户 Cookie 文件 |
| `yt-dlp` 更新频繁 | 版本落后会失效 | 后续提供更新机制或提示用户更新 |
| 打包体积增加 | 安装包变大 | 接受该成本，换取下载能力 |
| 杀毒误报 sidecar | 用户无法运行 | 文档说明并尽量使用可信打包方式 |
| Cookie 安全 | 敏感信息泄露风险 | Cookie 文件只在本地使用，不上传、不记录日志 |

## 11. 第一版 MVP 验收清单

| 检查项 | 必须通过 |
|---|---|
| 输入公开视频分享短链 | 是 |
| 下载到用户选择目录 | 是 |
| UI 展示下载中/成功/失败 | 是 |
| 失败时有明确原因 | 是 |
| 普通用户不需要手动安装开发环境 | 是 |
| 不要求手写平台解析 | 是 |

核心原则：

```text
先把真实视频下载跑通，再谈架构完整性。
```
