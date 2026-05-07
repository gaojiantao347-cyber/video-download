import { invoke } from '@tauri-apps/api/core';

import type { JsonRpcError, JsonRpcRequest, JsonRpcResponse, RpcMethod } from '../types/rpc';

const ENGINE_RPC_COMMAND = 'engine_rpc';
const JSON_RPC_VERSION = '2.0';

let requestSequence = 0;

export class EngineClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EngineClientError';
  }
}

export class EngineRpcError extends Error {
  readonly code: JsonRpcError['code'];
  readonly data?: unknown;

  constructor(error: JsonRpcError) {
    super(error.message);
    this.name = 'EngineRpcError';
    this.code = error.code;
    this.data = error.data;
  }
}

export async function callEngine<TResult, TParams = unknown>(
  method: RpcMethod,
  params?: TParams,
): Promise<TResult> {
  const request: JsonRpcRequest<TParams> = {
    jsonrpc: JSON_RPC_VERSION,
    id: nextRequestId(method),
    method,
    ...(params === undefined ? {} : { params }),
  };

  const response = await invoke<JsonRpcResponse<TResult>>(ENGINE_RPC_COMMAND, { request }).catch(
    (error: unknown) => {
      throw new EngineClientError(toErrorMessage(error));
    },
  );

  if (!isJsonRpcResponse<TResult>(response)) {
    throw new EngineClientError('下载引擎返回格式不正确');
  }

  if (response.id !== request.id) {
    throw new EngineClientError('下载引擎响应 ID 不匹配');
  }

  if (response.error) {
    throw new EngineRpcError(response.error);
  }

  return response.result;
}

function nextRequestId(method: RpcMethod): string {
  requestSequence = (requestSequence + 1) % Number.MAX_SAFE_INTEGER;
  return `${method}-${Date.now()}-${requestSequence}`;
}

function isJsonRpcResponse<TResult>(value: unknown): value is JsonRpcResponse<TResult> {
  if (!isRecord(value)) {
    return false;
  }

  if (value.jsonrpc !== JSON_RPC_VERSION || typeof value.id !== 'string') {
    return false;
  }

  return 'result' in value || isJsonRpcError(value.error);
}

function isJsonRpcError(value: unknown): value is JsonRpcError {
  return isRecord(value) && typeof value.code === 'string' && typeof value.message === 'string';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (isRecord(error) && typeof error.message === 'string') {
    return error.message;
  }

  return '下载引擎通信失败';
}
