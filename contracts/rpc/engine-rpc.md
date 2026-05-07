# Engine JSON-RPC 契约

## 传输约定

当前桌面端的 Engine RPC 是前端到 Tauri/Rust 的 facade：

```text
Vue -> Tauri invoke('engine_rpc') -> Rust EngineProcessManager
```

请求和响应仍使用 JSON-RPC 2.0 envelope，便于前端保持稳定调用形态。Rust 到 Python 下载引擎不是通用 JSON-RPC server，而是 CLI 参数 + stdout JSON 事件。

## 通用请求

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "method": "engine.healthCheck",
  "params": {}
}
```

## 通用成功响应

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "result": {}
}
```

## `engine.healthCheck`

检查 Rust 下载引擎 facade 是否可用。当前健康检查不启动真实下载，不等价于检测某个链接一定可下载。

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "health-1",
  "method": "engine.healthCheck",
  "params": {}
}
```

### 响应

```json
{
  "jsonrpc": "2.0",
  "id": "health-1",
  "result": {
    "version": "python-yt-dlp-bridge-0.1.0",
    "status": "RUNNING",
    "taskStore": "IN_MEMORY"
  }
}
```

`taskStore=IN_MEMORY` 表示当前任务状态只保存在 Rust 进程内；应用重启后不保留旧任务记录。

## `engine.getVersion`

返回当前本地下载引擎 facade 版本。

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "version-1",
  "method": "engine.getVersion",
  "params": {}
}
```

### 响应

```json
{
  "jsonrpc": "2.0",
  "id": "version-1",
  "result": {
    "version": "python-yt-dlp-bridge-0.1.0"
  }
}
```

## 相关 Schema

- `contracts/schemas/json-rpc-request.schema.json`
- `contracts/schemas/json-rpc-response.schema.json`
- `contracts/schemas/engine-health-response.schema.json`
- `contracts/schemas/engine-version-response.schema.json`
- `contracts/schemas/error-response.schema.json`
