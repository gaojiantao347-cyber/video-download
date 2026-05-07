import { defineStore } from 'pinia';

import {
  getSettings,
  selectDownloadDir as selectDownloadDirByDialog,
  updateSettings,
} from '../api/settingsApi';
import { mapUnknownErrorMessage } from '../api/errorMapper';
import {
  DEFAULT_SETTINGS,
  MAX_CONCURRENT_DOWNLOADS,
  MIN_CONCURRENT_DOWNLOADS,
  type AppSettings,
} from '../types/settings';

interface SettingsState {
  savedSettings: AppSettings;
  draftSettings: AppSettings;
  loading: boolean;
  saving: boolean;
  loaded: boolean;
  errorMessage: string | null;
}

function cloneSettings(settings: AppSettings): AppSettings {
  return { ...settings };
}

function isSameSettings(left: AppSettings, right: AppSettings): boolean {
  return (
    left.downloadDir === right.downloadDir &&
    left.maxConcurrentDownloads === right.maxConcurrentDownloads &&
    left.removeWatermark === right.removeWatermark &&
    left.allowFallback === right.allowFallback &&
    left.enableSystemNotifications === right.enableSystemNotifications
  );
}

export const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => ({
    savedSettings: cloneSettings(DEFAULT_SETTINGS),
    draftSettings: cloneSettings(DEFAULT_SETTINGS),
    loading: false,
    saving: false,
    loaded: false,
    errorMessage: null,
  }),
  getters: {
    dirty: (state): boolean => !isSameSettings(state.savedSettings, state.draftSettings),
    downloadDirChanged: (state): boolean =>
      state.savedSettings.downloadDir !== state.draftSettings.downloadDir,
    runtimeSettingsChanged: (state): boolean =>
      state.savedSettings.downloadDir !== state.draftSettings.downloadDir ||
      state.savedSettings.maxConcurrentDownloads !== state.draftSettings.maxConcurrentDownloads,
    removeWatermark: (state): boolean => state.savedSettings.removeWatermark,
    allowFallback: (state): boolean => state.savedSettings.allowFallback,
    enableSystemNotifications: (state): boolean => state.savedSettings.enableSystemNotifications,
  },
  actions: {
    async loadSettings(): Promise<void> {
      if (this.loading) {
        return;
      }

      this.loading = true;
      this.errorMessage = null;
      try {
        const settings = await getSettings();
        this.savedSettings = cloneSettings(settings);
        this.draftSettings = cloneSettings(settings);
        this.loaded = true;
      } catch (error) {
        this.errorMessage = mapUnknownErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    patchDraft(settings: Partial<AppSettings>): void {
      this.draftSettings = {
        ...this.draftSettings,
        ...settings,
      };
    },
    async selectDownloadDir(): Promise<void> {
      const selected = await selectDownloadDirByDialog(this.draftSettings.downloadDir);
      if (selected) {
        this.patchDraft({ downloadDir: selected });
      }
    },
    resetDraft(): void {
      this.draftSettings = cloneSettings(this.savedSettings);
      this.errorMessage = null;
    },
    restoreDefaultDraft(): void {
      this.draftSettings = cloneSettings(DEFAULT_SETTINGS);
      this.errorMessage = null;
    },
    validateDraft(): string | null {
      if (!this.draftSettings.downloadDir.trim()) {
        return '请选择下载目录';
      }

      if (
        !Number.isInteger(this.draftSettings.maxConcurrentDownloads) ||
        this.draftSettings.maxConcurrentDownloads < MIN_CONCURRENT_DOWNLOADS ||
        this.draftSettings.maxConcurrentDownloads > MAX_CONCURRENT_DOWNLOADS
      ) {
        return `并发限制必须是 ${MIN_CONCURRENT_DOWNLOADS}-${MAX_CONCURRENT_DOWNLOADS} 之间的整数`;
      }

      return null;
    },
    async saveSettings(): Promise<AppSettings> {
      const validationMessage = this.validateDraft();
      if (validationMessage) {
        this.errorMessage = validationMessage;
        throw new Error(validationMessage);
      }

      const previousSettings = cloneSettings(this.savedSettings);
      this.saving = true;
      this.errorMessage = null;
      try {
        const saved = await updateSettings(cloneSettings(this.draftSettings));
        this.savedSettings = cloneSettings(saved);
        this.draftSettings = cloneSettings(saved);
        this.loaded = true;
        return saved;
      } catch (error) {
        this.draftSettings = previousSettings;
        this.errorMessage = mapUnknownErrorMessage(error);
        throw error;
      } finally {
        this.saving = false;
      }
    },
  },
});
