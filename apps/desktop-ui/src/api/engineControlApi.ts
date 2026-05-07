import { invoke } from '@tauri-apps/api/core';

export function restartEngineProcess(): Promise<void> {
  return invoke('engine_restart');
}
