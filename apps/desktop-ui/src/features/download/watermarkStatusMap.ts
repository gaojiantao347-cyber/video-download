import type { WatermarkStatus } from '../../types/download';
import type { TaskStatusTagType } from './taskStatusMap';

export interface WatermarkStatusMeta {
  label: string;
  tagType: TaskStatusTagType;
  description: string;
}

export const WATERMARK_STATUS_MAP: Record<WatermarkStatus, WatermarkStatusMeta> = {
  NOT_REQUESTED: {
    label: '未请求去水印',
    tagType: 'info',
    description: '用户未开启优先无水印。',
  },
  REMOVED: {
    label: '已使用无水印资源',
    tagType: 'success',
    description: '已找到并使用无水印视频资源。',
  },
  UNAVAILABLE: {
    label: '无水印不可用',
    tagType: 'warning',
    description: '未找到可用无水印资源。',
  },
  FALLBACK: {
    label: '已降级普通下载',
    tagType: 'warning',
    description: '无水印不可用，已按设置降级下载普通资源。',
  },
  FAILED: {
    label: '去水印失败',
    tagType: 'danger',
    description: '去水印处理失败。',
  },
};

export function getWatermarkStatusMeta(status: WatermarkStatus): WatermarkStatusMeta {
  return WATERMARK_STATUS_MAP[status];
}
