import type { Platform } from '../../../types/download';

export type PlatformTagType = 'success' | 'warning' | 'info';

interface PlatformMeta {
  label: string;
  tagType: PlatformTagType;
  domains: readonly string[];
}

const PLATFORM_META_MAP: Record<Platform, PlatformMeta> = {
  DOUYIN: {
    label: '抖音',
    tagType: 'success',
    domains: ['douyin.com', 'iesdouyin.com'],
  },
  KUAISHOU: {
    label: '快手',
    tagType: 'warning',
    domains: ['kuaishou.com', 'gifshow.com'],
  },
};

export function detectPlatformFromUrl(url: string): Platform | null {
  const hostname = parseHostname(url);
  if (!hostname) {
    return null;
  }

  const matched = Object.entries(PLATFORM_META_MAP).find(([, meta]) =>
    meta.domains.some((domain) => isSameOrSubdomain(hostname, domain)),
  );

  return matched ? (matched[0] as Platform) : null;
}

export function getPlatformLabel(platform?: Platform | null): string {
  return platform ? PLATFORM_META_MAP[platform].label : '未知平台';
}

export function getPlatformTagType(platform?: Platform | null): PlatformTagType {
  return platform ? PLATFORM_META_MAP[platform].tagType : 'info';
}

export function getSupportedPlatformText(): string {
  return Object.values(PLATFORM_META_MAP)
    .map((meta) => meta.label)
    .join('、');
}

function parseHostname(url: string): string | null {
  const value = url.trim();
  if (!value) {
    return null;
  }

  try {
    const parsedUrl = new URL(value);
    if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
      return null;
    }
    return parsedUrl.hostname.toLowerCase();
  } catch {
    return null;
  }
}

function isSameOrSubdomain(hostname: string, domain: string): boolean {
  return hostname === domain || hostname.endsWith(`.${domain}`);
}
