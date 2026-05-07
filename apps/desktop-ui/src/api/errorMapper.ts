import type { ErrorCode } from '../types/errors';
import { ERROR_MESSAGE_MAP, FALLBACK_ERROR_MESSAGE } from './errorMessageMap';

interface ErrorLike {
  code?: unknown;
  message?: unknown;
}

export function mapErrorMessage(
  code?: ErrorCode | string | null,
  fallbackMessage?: string | null,
): string {
  if (fallbackMessage && code === 'DOWNLOAD_FAILED') {
    return fallbackMessage;
  }

  if (isErrorCode(code)) {
    return ERROR_MESSAGE_MAP[code];
  }

  return fallbackMessage || FALLBACK_ERROR_MESSAGE;
}

export function mapUnknownErrorMessage(error: unknown): string {
  if (isErrorLike(error)) {
    const code = typeof error.code === 'string' ? error.code : null;
    const message = typeof error.message === 'string' ? error.message : null;
    return mapErrorMessage(code, message);
  }

  if (error instanceof Error) {
    return error.message || FALLBACK_ERROR_MESSAGE;
  }

  if (typeof error === 'string') {
    return error || FALLBACK_ERROR_MESSAGE;
  }

  return FALLBACK_ERROR_MESSAGE;
}

export function isErrorCode(code?: string | null): code is ErrorCode {
  return Boolean(code && Object.prototype.hasOwnProperty.call(ERROR_MESSAGE_MAP, code));
}

function isErrorLike(error: unknown): error is ErrorLike {
  return typeof error === 'object' && error !== null;
}
