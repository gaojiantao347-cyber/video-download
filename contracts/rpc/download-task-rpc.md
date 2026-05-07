# Download Task JSON-RPC 契约

当前桌面端保留 `download.*` RPC 方法名作为前端稳定 facade，但实现链路已经迁移为：

```text
Vue -> Tauri invoke('engine_rpc') -> Rust EngineProcessManager -> Python CLI -> yt-dlp
```

Python 引擎通过 stdout 输出 JSON 事件，Rust 负责维护当前进程内任务状态。

## `download.createTask`

创建单个下载任务。Rust 层立即返回 `taskId`，随后启动 Python CLI 异步下载。

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `url` | string | 是 | 用户提交的公开视频分享链接 |
| `outputDir` | string | 是 | 下载输出目录 |
| `removeWatermark` | boolean | 是 | 是否优先尝试无水印/最佳可用资源 |
| `allowFallback` | boolean | 是 | 无水印资源不可用时是否允许降级普通下载 |

### 请求示例

```json
{
  "jsonrpc": "2.0",
  "id": "create-1",
  "method": "download.createTask",
  "params": {
    "url": "https://v.douyin.com/example/",
    "outputDir": "D:/Videos",
    "removeWatermark": true,
    "allowFallback": true
  }
}
```

### 响应示例

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

### 错误

| 错误码 | 场景 |
|---|---|
| `URL_EMPTY` | 链接为空 |
| `URL_INVALID` | URL 格式错误或非 HTTP(S) 链接 |
| `STORAGE_ERROR` | 下载目录不可用或文件系统异常 |
| `RPC_INVALID_REQUEST` | 请求参数缺失、类型错误或多余字段 |
| `RPC_INTERNAL_ERROR` | Python 下载引擎启动失败或内部异常 |

## `download.getTask`

查询当前桌面进程内任务状态、进度、文件信息和失败原因。

> 应用重启后，旧 `taskId` 返回 `TASK_NOT_FOUND` 是预期行为。跨重启历史记录属于后续功能。

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `taskId` | string | 是 | 下载任务 ID |

### 请求示例

```json
{
  "jsonrpc": "2.0",
  "id": "task-1",
  "method": "download.getTask",
  "params": {
    "taskId": "task-1770000000000-1"
  }
}
```

### 响应示例

```json
{
  "jsonrpc": "2.0",
  "id": "task-1",
  "result": {
    "taskId": "task-1770000000000-1",
    "sourceUrl": "https://v.douyin.com/example/",
    "platform": "DOUYIN",
    "title": "视频标题",
    "author": null,
    "coverUrl": null,
    "removeWatermark": true,
    "watermarkStatus": "UNAVAILABLE",
    "status": "DOWNLOADING",
    "progress": 45,
    "fileName": "视频标题.mp4",
    "filePath": null,
    "errorCode": null,
    "errorMessage": null,
    "createdAt": "2026-04-28T12:00:00.000Z",
    "updatedAt": "2026-04-28T12:00:30.000Z"
  }
}
```

### 错误

| 错误码 | 场景 |
|---|---|
| `TASK_NOT_FOUND` | 当前进程内不存在该任务 |
| `RPC_INVALID_REQUEST` | 请求参数缺失、类型错误或多余字段 |
| `RPC_INTERNAL_ERROR` | 任务表锁或内部状态异常 |

## `download.getFile`

获取已完成任务的本地文件信息。该方法不传输文件字节，只返回 Rust 校验过的本地文件路径，供桌面端通过 Tauri 打开文件或所在目录。

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `taskId` | string | 是 | 下载任务 ID |

### 响应示例

```json
{
  "jsonrpc": "2.0",
  "id": "file-1",
  "result": {
    "taskId": "task-1770000000000-1",
    "fileName": "视频标题.mp4",
    "filePath": "D:/Videos/视频标题.mp4"
  }
}
```

### 错误

| 错误码 | 场景 |
|---|---|
| `TASK_NOT_FOUND` | 当前进程内不存在该任务 |
| `FILE_NOT_READY` | 任务尚未成功 |
| `FILE_NOT_FOUND` | 任务成功但本地文件不存在或路径缺失 |
| `RPC_INTERNAL_ERROR` | 任务表锁或内部状态异常 |

## 状态枚举

当前 Rust/Python 主链路产生：`PENDING`、`DOWNLOADING`、`SUCCESS`、`FAILED`。

去水印状态：`NOT_REQUESTED`、`REMOVED`、`UNAVAILABLE`、`FALLBACK`、`FAILED`。

## 相关 Schema

- `contracts/schemas/create-download-task-request.schema.json`
- `contracts/schemas/create-download-task-response.schema.json`
- `contracts/schemas/get-download-task-request.schema.json`
- `contracts/schemas/download-task.schema.json`
- `contracts/schemas/get-download-file-request.schema.json`
- `contracts/schemas/download-file.schema.json`
- `contracts/schemas/error-response.schema.json`
