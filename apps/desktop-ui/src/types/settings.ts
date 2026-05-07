export interface AppSettings {
  downloadDir: string;
  maxConcurrentDownloads: number;
  removeWatermark: boolean;
  allowFallback: boolean;
  enableSystemNotifications: boolean;
}

export type UpdateSettingsRequest = AppSettings;

export const MIN_CONCURRENT_DOWNLOADS = 1;
export const MAX_CONCURRENT_DOWNLOADS = 4;

export const DEFAULT_SETTINGS: AppSettings = {
  downloadDir: '',
  maxConcurrentDownloads: 2,
  removeWatermark: true,
  allowFallback: true,
  enableSystemNotifications: false,
};
