# Engine MVP 错误码

错误码由本地下载引擎稳定维护，前端只依赖 `code` 做展示和分支处理。已有错误码不重命名；语义随 Python + yt-dlp 主链路保持稳定。

| 错误码 | 默认文案 | 场景 |
|---|---|---|
| `URL_EMPTY` | 链接不能为空 | 用户未提交 URL |
| `URL_INVALID` | 链接格式不正确 | URL 不是合法 HTTP(S) 链接 |
| `PLATFORM_NOT_SUPPORTED` | 暂不支持该平台 | 当前产品/前端限制范围外的链接；不代表 yt-dlp 能力上限 |
| `URL_EXPIRED` | 视频链接已失效 | 短链、落地页或公开视频资源不可访问 |
| `PARSE_FAILED` | 视频解析失败 | 下载引擎或上游 extractor 获取视频信息失败 |
| `WATERMARK_REMOVE_UNAVAILABLE` | 未找到可用无水印视频资源 | 请求去水印且不允许降级，当前资源不可满足 |
| `DOWNLOAD_FAILED` | 视频下载失败 | Python/yt-dlp 下载失败、平台规则变化或链接不可访问 |
| `FILE_TOO_LARGE` | 视频文件超过大小限制 | 超过本地配置的最大文件大小 |
| `FILE_NOT_FOUND` | 文件不存在或已被清理 | 查询或访问已完成文件时本地文件缺失 |
| `TASK_NOT_FOUND` | 下载任务不存在 | 当前进程内不存在该下载任务，应用重启后的旧任务也会触发该错误 |
| `FILE_NOT_READY` | 文件尚未下载完成 | 任务未成功时请求访问下载文件 |
| `STORAGE_ERROR` | 本地存储异常 | 下载目录、配置文件或本地文件系统操作失败 |
| `RPC_INVALID_REQUEST` | JSON-RPC 请求格式不正确 | JSON 解析失败、协议版本错误、缺少必要字段 |
| `RPC_METHOD_NOT_FOUND` | JSON-RPC 方法不存在 | 请求的 RPC 方法未注册 |
| `RPC_INTERNAL_ERROR` | JSON-RPC 内部错误 | RPC handler 执行异常、Python 引擎启动失败或内部状态异常 |

## JSON-RPC 错误格式

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": "URL_INVALID",
    "message": "链接格式不正确",
    "data": null
  }
}
```

## 兼容规则

- 不重命名已有错误码。
- 不改变前端分支所依赖的错误码标识。
- 新平台、新能力只能追加错误码。
- 用户可读文案可以优化，但 `code` 必须稳定。
