import type { ErrorCode } from './errors';

export type RpcMethod =
  | 'engine.healthCheck'
  | 'engine.getVersion'
  | 'settings.get'
  | 'settings.update'
  | 'download.createTask'
  | 'download.getTask'
  | 'download.getFile';

export interface JsonRpcRequest<TParams = unknown> {
  jsonrpc: '2.0';
  id: string;
  method: RpcMethod;
  params?: TParams;
}

export interface JsonRpcError {
  code: ErrorCode | string;
  message: string;
  data?: unknown;
}

export type JsonRpcResponse<TResult = unknown> =
  | {
      jsonrpc: '2.0';
      id: string;
      result: TResult;
      error?: never;
    }
  | {
      jsonrpc: '2.0';
      id: string;
      result?: never;
      error: JsonRpcError;
    };
