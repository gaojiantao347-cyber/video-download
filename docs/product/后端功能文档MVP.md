# 后端功能文档 MVP

版本：V1.1  
日期：2026-04-28

## 1. MVP 目标

第一版后端只做一个简单、可维护的视频下载工具，不做大而全的视频平台爬虫。

核心能力：

```text
接收公开视频分享链接 -> Rust 创建当前会话任务 -> Python/yt-dlp 解析并下载 -> 回传进度事件 -> 提供任务状态和本地文件路径
```

## 2. 功能边界

### 2.1 MVP 支持

| 功能           | 说明                                                           |
| -------------- | -------------------------------------------------------------- |
| 单链接下载     | 每次提交一个视频分享链接                                       |
| 支持平台       | 抖音、快手                                                     |
| 短链/平台解析  | 由 `yt-dlp` extractor 处理公开视频链接                         |
| 视频元数据解析 | 尽量获取标题、作者、封面；不承诺返回视频直链                   |
| 去水印下载     | 作为 best-effort 下载偏好，能拿到最佳可用资源则优先保存         |
| 普通下载降级   | 无水印资源不可用时，可按配置降级为普通下载                     |
| 下载任务管理   | 创建任务、更新状态、记录失败原因                               |
| 下载进度统计   | 根据已下载字节数计算百分比                                     |
| 本地文件保存   | 保存到服务端本地目录                                           |
| 文件访问接口   | 前端可通过 taskId 获取 Rust 校验过的本地文件路径               |
| 基础异常处理   | 链接无效、平台不支持、解析失败、下载失败、无水印不可用         |

### 2.2 MVP 不支持

| 功能                | 是否支持 | 原因                                |
| ------------------- | -------: | ----------------------------------- |
| 用户系统            |   不支持 | 第一版没有必要                      |
| 数据库持久化        | 不支持 | 当前为 Rust 内存任务状态 + 本地文件；跨重启历史记录后续再做 |
| 批量下载            |   不支持 | MVP 先跑通单链接                    |
| 分布式任务队列      |   不支持 | 单机任务足够                        |
| Redis/Kafka         |   不支持 | 当前是过度设计                      |
| 登录态 Cookie/Token |   不支持 | 不处理权限绕过                      |
| 私密/付费/DRM 视频  |   不支持 | 不做访问控制绕过                    |
| 反风控/验证码绕过   |   不支持 | 不做规避平台限制的能力              |
| 画面级水印修复      |   不支持 | MVP 不做裁剪、模糊、AI 修复等重处理 |

> 去水印能力只面向用户有权下载和使用的公开视频内容。后端不提供 DRM、付费、私密权限、验证码等绕过能力。

## 3. 后端模块规划

| 模块 | 职责 | MVP 是否必须 |
|---|---|---:|
| Rust RPC facade | 接收 `engine_rpc` JSON-RPC envelope、校验参数、路由方法 | 是 |
| Rust 任务状态 | 维护当前进程内任务状态、进度、错误、文件路径 | 是 |
| Python 下载引擎 | 调用 `yt-dlp` 下载视频并输出 JSON 事件 | 是 |
| 设置模块 | 读取/保存 `settings.json`，管理下载目录和偏好 | 是 |
| 文件访问模块 | 校验任务状态和本地文件存在性，返回安全文件路径 | 是 |
| 异常处理模块 | 统一返回错误码和错误信息 | 是 |
| 历史记录模块 | 跨重启持久化下载历史 | 否 |

## 4. 核心数据模型

### 4.1 下载任务

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `taskId` | String | 任务 ID |
| `sourceUrl` | String | 用户提交的原始链接 |
| `platform` | String | `DOUYIN` / `KUAISHOU` |
| `title` | String | 视频标题 |
| `author` | String | 作者昵称 |
| `coverUrl` | String | 封面地址 |
| `removeWatermark` | Boolean | 用户是否请求去水印 |
| `watermarkStatus` | String | `NOT_REQUESTED` / `REMOVED` / `UNAVAILABLE` / `FALLBACK` / `FAILED` |
| `status` | String | 任务状态 |
| `progress` | Integer | 下载进度，0-100 |
| `fileName` | String | 保存文件名 |
| `filePath` | String | 本地保存路径 |
| `errorMessage` | String | 失败原因 |
| `createdAt` | DateTime | 创建时间 |
| `updatedAt` | DateTime | 更新时间 |

### 4.2 元数据边界

当前主链路尽量返回 `title`、`author`、`coverUrl` 供前端展示；视频真实资源选择、短链处理和下载由 `yt-dlp` 完成，产品层不承诺输出视频直链。

## 5. 任务状态设计

| 状态          | 说明                         |
| ------------- | ---------------------------- |
| `PENDING`     | 已创建，等待执行 |
| `DOWNLOADING` | 正在下载视频文件 |
| `SUCCESS`     | 下载成功 |
| `FAILED`      | 下载失败 |

## 6. 下载核心接口设计

下载核心收敛为 Python CLI：

```text
vd-engine --url <url> --output-dir <dir> --remove-watermark <bool> --allow-fallback <bool>
```

Python 引擎通过 stdout 输出 JSON 事件，Rust 负责转换为 `DownloadTask` 状态。平台解析、短链处理和真实下载交给 `yt-dlp`，项目不再从 HTML/script/JSON 中自研抽取视频直链。

## 7. 去水印能力设计

### 7.1 MVP 去水印策略

MVP 不做视频画面处理，也不承诺自研无水印直链抽取。`removeWatermark=true` 作为下载偏好传给本地下载核心，最终能否拿到无水印/最佳可用资源由 `yt-dlp` 和平台公开视频资源决定。

| 策略 | 说明 | MVP 是否支持 |
|---|---|---:|
| best-effort 最佳可用资源 | 优先让 `yt-dlp` 选择最佳可用格式 | 是 |
| 普通下载降级 | 无法满足去水印偏好时，按 `allowFallback` 降级普通下载 | 是 |
| `VIDEO_POST_PROCESSING` | 下载后裁剪、模糊、覆盖、AI 修复水印 | 否 |

### 7.2 去水印结果状态

| 状态            | 说明                         |
| --------------- | ---------------------------- |
| `NOT_REQUESTED` | 用户未请求去水印             |
| `REMOVED`       | 已使用无水印资源下载         |
| `UNAVAILABLE`   | 未找到可用无水印资源         |
| `FALLBACK`      | 无水印不可用，已降级普通下载 |
| `FAILED`        | 去水印处理失败               |

### 7.3 降级规则

| 配置                  | 行为                                 |
| --------------------- | ------------------------------------ |
| `allowFallback=true`  | 无水印不可用时继续下载普通版本       |
| `allowFallback=false` | 无水印不可用时任务失败，返回明确错误 |

## 8. API 设计

当前桌面端不暴露 HTTP API。Vue 通过 Tauri `invoke('engine_rpc')` 发送 JSON-RPC envelope。

### 8.1 创建下载任务

```json
{
  "jsonrpc": "2.0",
  "id": "create-1",
  "method": "download.createTask",
  "params": {
    "url": "https://v.douyin.com/xxxxxx/",
    "outputDir": "D:/Videos",
    "removeWatermark": true,
    "allowFallback": true
  }
}
```

响应：

```json
{
  "jsonrpc": "2.0",
  "id": "create-1",
  "result": {
    "taskId": "task-1770000000000-1",
    "status": "PENDING",
    "removeWatermark": true
  }
}
```

### 8.2 查询任务状态

调用 `download.getTask`，只查询当前 Rust 进程内任务。应用重启后的旧 `taskId` 返回 `TASK_NOT_FOUND` 属于预期。

### 8.3 获取本地文件信息

调用 `download.getFile`。该方法不传输文件字节，只返回 Rust 校验过的本地文件路径，供桌面端打开文件或所在目录。

说明：

- 仅当任务状态为 `SUCCESS` 时允许访问文件路径。
- 文件不存在时返回明确错误。
- MVP 不提供删除任务记录接口。

## 9. 下载流程

```text
创建任务
  ↓
Rust 校验 URL、outputDir、去水印偏好
  ↓
状态进入 PENDING / DOWNLOADING
  ↓
Rust 启动 Python vd-engine
  ↓
Python 调用 yt-dlp 处理平台解析、短链和下载
  ↓
stdout 输出进度 / 完成 / 失败 JSON 事件
  ↓
Rust 更新当前进程内 DownloadTask
  ↓
成功：状态改为 SUCCESS，记录 filePath
失败：状态改为 FAILED，并记录 errorCode/errorMessage
```

## 10. 配置项

| 配置项 | 默认值 | 说明 |
|---|---:|---|
| `downloadDir` | 用户视频目录 | 文件保存目录 |
| `maxConcurrentDownloads` | `2` | 最大并发下载数，MVP 限制 1 到 4 |
| `removeWatermark` | `true` | 新任务默认是否优先尝试无水印/最佳可用资源 |
| `allowFallback` | `true` | 无水印不可用时是否降级普通下载 |
| `enableSystemNotifications` | `false` | 是否启用系统通知 |

## 11. 异常处理

| 场景             | 建议错误码                     | 返回信息                 |
| ---------------- | ------------------------------ | ------------------------ |
| 链接为空         | `URL_EMPTY`                    | 链接不能为空             |
| URL 格式错误     | `URL_INVALID`                  | 链接格式不正确           |
| 平台不支持       | `PLATFORM_NOT_SUPPORTED`       | 暂不支持该平台           |
| 链接已失效       | `URL_EXPIRED`                  | 视频链接已失效           |
| 解析失败         | `PARSE_FAILED`                 | 视频解析失败             |
| 无水印资源不可用 | `WATERMARK_REMOVE_UNAVAILABLE` | 未找到可用无水印视频资源 |
| 去水印不可满足   | `WATERMARK_REMOVE_UNAVAILABLE` | 未找到可用无水印视频资源 |
| 下载失败         | `DOWNLOAD_FAILED`              | 视频下载失败             |
| 文件过大         | `FILE_TOO_LARGE`               | 视频文件超过大小限制     |
| 文件不存在       | `FILE_NOT_FOUND`               | 文件不存在或已被清理     |
| 本地存储异常     | `STORAGE_ERROR`                | 下载目录或配置文件异常   |

## 12. 存储规则

| 规则         | 说明                                    |
| ------------ | --------------------------------------- |
| 文件目录     | 默认保存到 `downloads/{platform}/`      |
| 文件名       | 使用标题生成，非法字符统一替换为 `_`    |
| 去水印文件名 | 去水印成功时可追加 `_no_watermark` 后缀 |
| 重名处理     | 文件名后追加 taskId 后缀                |
| 文件类型     | 默认保存为 `.mp4`                       |
| 路径安全     | 禁止用户输入影响最终保存路径            |

## 13. 验收标准

| 编号      | 验收项                                     |
| --------- | ------------------------------------------ |
| B-MVP-001 | 可以创建单个下载任务                       |
| B-MVP-002 | 可以识别抖音、快手链接                     |
| B-MVP-003 | 可以处理短链跳转                           |
| B-MVP-004 | 可以尽量获取公开视频标题、作者、封面；不承诺输出视频直链 |
| B-MVP-005 | 可以按 best-effort 优先下载最佳可用资源     |
| B-MVP-006 | 无水印资源不可用时能按配置降级或失败       |
| B-MVP-007 | 可以下载视频到本地目录                     |
| B-MVP-008 | 可以查询任务状态、下载进度、去水印状态     |
| B-MVP-009 | 下载成功后可以通过接口获取本地文件路径     |
| B-MVP-010 | 失败时能返回明确错误信息                   |
| B-MVP-011 | 不提供批量抓取、登录态输入、权限绕过能力   |
