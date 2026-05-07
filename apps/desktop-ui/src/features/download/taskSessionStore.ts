import { defineStore } from 'pinia';

import type {
  CreateDownloadTaskRequest,
  CreateDownloadTaskResponse,
  DownloadTask,
  DownloadTaskStatus,
} from '../../types/download';
import { isRunningTaskStatus } from './taskStatusMap';

const MAX_SESSION_TASKS = 10;

export interface DownloadTaskSessionItem {
  taskId: string;
  request: CreateDownloadTaskRequest;
  status: DownloadTaskStatus;
  task: DownloadTask | null;
  createdAt: string;
  updatedAt: string;
}

interface DownloadTaskSessionState {
  activeTaskId: string | null;
  items: DownloadTaskSessionItem[];
}

function createFallbackRequest(task: DownloadTask): CreateDownloadTaskRequest {
  return {
    url: task.sourceUrl,
    outputDir: '',
    removeWatermark: task.removeWatermark,
    allowFallback: task.watermarkStatus === 'FALLBACK',
  };
}

function trimItems(items: DownloadTaskSessionItem[]): DownloadTaskSessionItem[] {
  return items.slice(0, MAX_SESSION_TASKS);
}

export const useDownloadTaskSessionStore = defineStore('downloadTaskSession', {
  state: (): DownloadTaskSessionState => ({
    activeTaskId: null,
    items: [],
  }),
  getters: {
    activeItem: (state): DownloadTaskSessionItem | null =>
      state.items.find((item) => item.taskId === state.activeTaskId) ?? null,
    activeTask(): DownloadTask | null {
      return this.activeItem?.task ?? null;
    },
    hasRunningTasks: (state): boolean =>
      state.items.some((item) => isRunningTaskStatus(item.task?.status ?? item.status)),
  },
  actions: {
    setActiveTask(taskId: string): void {
      this.activeTaskId = taskId;
    },
    addCreatedTask(response: CreateDownloadTaskResponse, request: CreateDownloadTaskRequest): void {
      const now = new Date().toISOString();
      const existingIndex = this.items.findIndex((item) => item.taskId === response.taskId);
      const item: DownloadTaskSessionItem = {
        taskId: response.taskId,
        request,
        status: response.status,
        task: null,
        createdAt: now,
        updatedAt: now,
      };

      if (existingIndex >= 0) {
        this.items.splice(existingIndex, 1);
      }

      this.items = trimItems([item, ...this.items]);
      this.activeTaskId = response.taskId;
    },
    upsertTask(task: DownloadTask): void {
      const existingIndex = this.items.findIndex((item) => item.taskId === task.taskId);
      const now = new Date().toISOString();

      if (existingIndex >= 0) {
        const existing = this.items[existingIndex];
        this.items.splice(existingIndex, 1, {
          ...existing,
          status: task.status,
          task,
          updatedAt: now,
        });
        return;
      }

      this.items = trimItems([
        {
          taskId: task.taskId,
          request: createFallbackRequest(task),
          status: task.status,
          task,
          createdAt: task.createdAt,
          updatedAt: now,
        },
        ...this.items,
      ]);
    },
    getRequest(taskId: string): CreateDownloadTaskRequest | null {
      return this.items.find((item) => item.taskId === taskId)?.request ?? null;
    },
  },
});
