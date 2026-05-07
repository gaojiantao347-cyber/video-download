import type { Platform } from '../../../types/download';
import type { ErrorCode } from '../../../types/errors';
import { detectPlatformFromUrl } from './platform';

export interface DownloadUrlValidationResult {
  valid: boolean;
  normalizedUrl: string;
  platform: Platform | null;
  errorCode?: ErrorCode;
}

export function validateDownloadUrl(url: string): DownloadUrlValidationResult {
  const normalizedUrl = url.trim();

  if (!normalizedUrl) {
    return invalid(normalizedUrl, 'URL_EMPTY');
  }

  if (!isHttpUrl(normalizedUrl)) {
    return invalid(normalizedUrl, 'URL_INVALID');
  }

  const platform = detectPlatformFromUrl(normalizedUrl);
  if (!platform) {
    return invalid(normalizedUrl, 'PLATFORM_NOT_SUPPORTED');
  }

  return {
    valid: true,
    normalizedUrl,
    platform,
  };
}

function invalid(normalizedUrl: string, errorCode: ErrorCode): DownloadUrlValidationResult {
  return {
    valid: false,
    normalizedUrl,
    platform: null,
    errorCode,
  };
}

function isHttpUrl(url: string): boolean {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:';
  } catch {
    return false;
  }
}
