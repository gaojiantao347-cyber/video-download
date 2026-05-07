import { CircleCheck, CircleClose, Clock, VideoPlay } from '@element-plus/icons-vue';
import type { Component } from 'vue';

import type { DownloadTaskStatus } from '../../types/download';

export type TaskStatusTagType = 'primary' | 'success' | 'warning' | 'info' | 'danger';
export type TaskProgressStatus = 'success' | 'warning' | 'exception' | undefined;

export interface TaskStatusMeta {
  label: string;
  tagType: TaskStatusTagType;
  icon: Component;
  description: string;
  progressStatus: TaskProgressStatus;
}

export const TASK_STATUS_MAP: Record<DownloadTaskStatus, TaskStatusMeta> = {
  PENDING: {
    label: '等待下载',
    tagType: 'info',
    icon: Clock,
    description: '任务已创建，等待引擎处理。',
    progressStatus: undefined,
  },
  DOWNLOADING: {
    label: '正在下载',
    tagType: 'primary',
    icon: VideoPlay,
    description: '正在保存视频文件到本地。',
    progressStatus: undefined,
  },
  SUCCESS: {
    label: '下载完成',
    tagType: 'success',
    icon: CircleCheck,
    description: '任务已完成，可以打开文件或所在目录。',
    progressStatus: 'success',
  },
  FAILED: {
    label: '下载失败',
    tagType: 'danger',
    icon: CircleClose,
    description: '任务执行失败，请查看失败原因后重试。',
    progressStatus: 'exception',
  },
};

export function getTaskStatusMeta(status: DownloadTaskStatus): TaskStatusMeta {
  return TASK_STATUS_MAP[status];
}

export function isRunningTaskStatus(status?: DownloadTaskStatus | null): boolean {
  return status === 'PENDING' || status === 'DOWNLOADING';
}

export function isTerminalTaskStatus(status?: DownloadTaskStatus | null): boolean {
  return status === 'SUCCESS' || status === 'FAILED';
}
