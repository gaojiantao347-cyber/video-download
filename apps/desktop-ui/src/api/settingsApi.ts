import { open } from '@tauri-apps/plugin-dialog';

import type { AppSettings, UpdateSettingsRequest } from '../types/settings';
import { callEngine } from './engineClient';

export function getSettings(): Promise<AppSettings> {
  return callEngine<AppSettings, Record<string, never>>('settings.get', {});
}

export function updateSettings(settings: UpdateSettingsRequest): Promise<AppSettings> {
  return callEngine<AppSettings, UpdateSettingsRequest>('settings.update', settings);
}

export async function selectDownloadDir(currentDir?: string): Promise<string | null> {
  const selected = await open({
    title: '选择下载目录',
    directory: true,
    multiple: false,
    defaultPath: currentDir || undefined,
  });

  if (Array.isArray(selected)) {
    return selected[0] ?? null;
  }

  return selected;
}
