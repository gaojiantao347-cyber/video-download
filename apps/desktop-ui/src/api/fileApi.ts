import { invoke } from '@tauri-apps/api/core';

export function openDownloadFile(taskId: string): Promise<void> {
  return invoke('open_download_file', { taskId });
}

export function revealDownloadFile(taskId: string): Promise<void> {
  return invoke('reveal_download_file', { taskId });
}
