import type { ErrorCode } from './errors';

export type Platform = 'DOUYIN' | 'KUAISHOU';

export type DownloadTaskStatus = 'PENDING' | 'DOWNLOADING' | 'SUCCESS' | 'FAILED';

export type WatermarkStatus = 'NOT_REQUESTED' | 'REMOVED' | 'UNAVAILABLE' | 'FALLBACK' | 'FAILED';

export type CookiesFromBrowser = 'edge' | 'chrome' | 'firefox';

export interface CreateDownloadTaskRequest {
  url: string;
  outputDir: string;
  removeWatermark: boolean;
  allowFallback: boolean;
  cookiesFromBrowser?: CookiesFromBrowser;
}

export interface CreateDownloadTaskResponse {
  taskId: string;
  status: 'PENDING';
  removeWatermark: boolean;
}

export interface DownloadTask {
  taskId: string;
  sourceUrl: string;
  platform?: Platform | null;
  title?: string | null;
  author?: string | null;
  coverUrl?: string | null;
  removeWatermark: boolean;
  watermarkStatus: WatermarkStatus;
  status: DownloadTaskStatus;
  progress: number;
  fileName?: string | null;
  filePath?: string | null;
  errorCode?: Exclude<
    ErrorCode,
    | 'RPC_INVALID_REQUEST'
    | 'RPC_METHOD_NOT_FOUND'
    | 'RPC_INTERNAL_ERROR'
    | 'TASK_NOT_FOUND'
    | 'FILE_NOT_READY'
  > | null;
  errorMessage?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface DownloadFile {
  taskId: string;
  fileName: string;
  filePath: string;
}
