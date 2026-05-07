export type EngineRuntimeStatus = 'STARTING' | 'RUNNING' | 'STOPPING' | 'FAILED';

export type EngineTaskStoreStatus = 'IN_MEMORY';

export type EngineConnectionStatus = 'starting' | 'ready' | 'disconnected' | 'error';

export interface EngineHealthResponse {
  version: string;
  status: EngineRuntimeStatus;
  taskStore: EngineTaskStoreStatus;
}

export interface EngineVersionResponse {
  version: string;
}
