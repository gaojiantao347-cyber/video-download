import type { ErrorCode } from '../types/errors';

export const FALLBACK_ERROR_MESSAGE = '操作失败，请稍后重试';

export const ERROR_MESSAGE_MAP: Record<ErrorCode, string> = {
  URL_EMPTY: '请输入视频分享链接',
  URL_INVALID: '请输入合法的 http/https 链接',
  PLATFORM_NOT_SUPPORTED: '当前仅支持抖音、快手公开视频链接',
  URL_EXPIRED: '视频链接可能已失效',
  PARSE_FAILED: '视频解析失败，请检查链接是否公开可访问',
  WATERMARK_REMOVE_UNAVAILABLE: '未找到可用无水印资源',
  DOWNLOAD_FAILED: '视频下载失败，请稍后重试',
  FILE_TOO_LARGE: '视频文件超过大小限制',
  FILE_NOT_FOUND: '文件不存在或已被清理',
  TASK_NOT_FOUND: '下载任务不存在，请重新创建任务',
  FILE_NOT_READY: '文件尚未下载完成，请等待任务完成后再操作',
  STORAGE_ERROR: '本地存储异常，请检查下载目录权限',
  RPC_INVALID_REQUEST: '引擎请求格式不正确',
  RPC_METHOD_NOT_FOUND: '当前引擎暂不支持该能力',
  RPC_INTERNAL_ERROR: '引擎内部错误，请稍后重试',
};
