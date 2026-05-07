import { defineStore } from 'pinia';

import { restartEngineProcess } from '../api/engineControlApi';
import { mapUnknownErrorMessage } from '../api/errorMapper';
import type {
  EngineConnectionStatus,
  EngineHealthResponse,
  EngineRuntimeStatus,
} from '../types/engine';

interface EngineState {
  status: EngineConnectionStatus;
  version: string | null;
  errorMessage: string | null;
  lastCheckedAt: string | null;
  health: EngineHealthResponse | null;
  restarting: boolean;
}

const ENGINE_STATUS_TEXT: Record<EngineConnectionStatus, string> = {
  starting: '引擎启动中',
  ready: '引擎可用',
  disconnected: '引擎未连接',
  error: '引擎异常',
};

function mapRuntimeStatus(status: EngineRuntimeStatus): EngineConnectionStatus {
  if (status === 'RUNNING') {
    return 'ready';
  }

  if (status === 'STARTING' || status === 'STOPPING') {
    return 'starting';
  }

  return 'error';
}

export const useEngineStore = defineStore('engine', {
  state: (): EngineState => ({
    status: 'disconnected',
    version: null,
    errorMessage: null,
    lastCheckedAt: null,
    health: null,
    restarting: false,
  }),
  getters: {
    statusText: (state): string => ENGINE_STATUS_TEXT[state.status],
  },
  actions: {
    setStarting(): void {
      this.status = 'starting';
      this.errorMessage = null;
    },
    setHealth(health: EngineHealthResponse): void {
      this.health = health;
      this.version = health.version;
      this.status = mapRuntimeStatus(health.status);
      this.errorMessage = health.status === 'FAILED' ? '下载引擎启动失败' : null;
      this.lastCheckedAt = new Date().toISOString();
    },
    setDisconnected(): void {
      this.status = 'disconnected';
      this.health = null;
      this.errorMessage = null;
      this.lastCheckedAt = new Date().toISOString();
    },
    setError(message: string): void {
      this.status = 'error';
      this.errorMessage = message;
      this.lastCheckedAt = new Date().toISOString();
    },
    async restartEngine(): Promise<void> {
      this.restarting = true;
      this.status = 'starting';
      this.errorMessage = null;
      try {
        await restartEngineProcess();
      } catch (error) {
        const message = mapUnknownErrorMessage(error);
        this.setError(message);
        throw error;
      } finally {
        this.restarting = false;
      }
    },
  },
});
