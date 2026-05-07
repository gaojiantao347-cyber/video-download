import { callEngine } from './engineClient';
import type {
  CreateDownloadTaskRequest,
  CreateDownloadTaskResponse,
  DownloadFile,
  DownloadTask,
} from '../types/download';

interface GetDownloadTaskRequest {
  taskId: string;
}

interface GetDownloadFileRequest {
  taskId: string;
}

export function createDownloadTask(
  params: CreateDownloadTaskRequest,
): Promise<CreateDownloadTaskResponse> {
  return callEngine<CreateDownloadTaskResponse, CreateDownloadTaskRequest>(
    'download.createTask',
    params,
  );
}

export function retryDownloadTask(
  params: CreateDownloadTaskRequest,
): Promise<CreateDownloadTaskResponse> {
  return createDownloadTask(params);
}

export function getDownloadTask(taskId: string): Promise<DownloadTask> {
  return callEngine<DownloadTask, GetDownloadTaskRequest>('download.getTask', { taskId });
}

export function getDownloadFile(taskId: string): Promise<DownloadFile> {
  return callEngine<DownloadFile, GetDownloadFileRequest>('download.getFile', { taskId });
}
