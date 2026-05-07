# Settings JSON-RPC 契约

当前桌面端设置由 Tauri/Rust facade 持久化到应用配置目录中的 `settings.json`。Vue 前端必须通过 Tauri 转发 JSON-RPC 调用，不直接读写本地文件。

## `settings.get`

读取当前应用设置。

### 请求参数

无业务参数，调用方传空对象 `{}`。

### 请求示例

```json
{
  "jsonrpc": "2.0",
  "id": "settings-get-1",
  "method": "settings.get",
  "params": {}
}
```

### 响应示例

```json
{
  "jsonrpc": "2.0",
  "id": "settings-get-1",
  "result": {
    "downloadDir": "D:/Videos/video-download",
    "maxConcurrentDownloads": 2,
    "removeWatermark": true,
    "allowFallback": true,
    "enableSystemNotifications": false
  }
}
```

## `settings.update`

保存基础设置。新下载目录和下载偏好会影响后续创建的新任务。

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `downloadDir` | string | 是 | 下载目录，必须非空 |
| `maxConcurrentDownloads` | integer | 是 | 下载并发数，MVP 限制为 `1` 到 `4` |
| `removeWatermark` | boolean | 是 | 新任务默认是否优先尝试无水印/最佳可用资源 |
| `allowFallback` | boolean | 是 | 无水印不可用时是否默认降级普通下载 |
| `enableSystemNotifications` | boolean | 是 | 桌面端是否启用系统通知 |

### 请求示例

```json
{
  "jsonrpc": "2.0",
  "id": "settings-update-1",
  "method": "settings.update",
  "params": {
    "downloadDir": "D:/Videos/video-download",
    "maxConcurrentDownloads": 2,
    "removeWatermark": true,
    "allowFallback": true,
    "enableSystemNotifications": true
  }
}
```

### 响应示例

```json
{
  "jsonrpc": "2.0",
  "id": "settings-update-1",
  "result": {
    "downloadDir": "D:/Videos/video-download",
    "maxConcurrentDownloads": 2,
    "removeWatermark": true,
    "allowFallback": true,
    "enableSystemNotifications": true
  }
}
```

### 错误

| 错误码 | 场景 |
|---|---|
| `RPC_INVALID_REQUEST` | 参数缺失、类型错误或并发越界 |
| `STORAGE_ERROR` | 本地配置保存、配置目录创建或下载目录创建失败 |

## 相关 Schema

- `contracts/schemas/app-settings.schema.json`
- `contracts/schemas/update-settings-request.schema.json`
- `contracts/schemas/error-response.schema.json`
