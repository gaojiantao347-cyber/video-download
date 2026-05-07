import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from '@tauri-apps/plugin-notification';

export async function ensureNotificationPermission(): Promise<boolean> {
  if (await isPermissionGranted()) {
    return true;
  }

  const permission = await requestPermission();
  return permission === 'granted';
}

export async function sendDownloadSuccessNotification(message: string): Promise<void> {
  if (!(await isPermissionGranted())) {
    return;
  }

  sendNotification({
    title: '下载完成',
    body: message,
  });
}

export async function sendDownloadFailureNotification(message: string): Promise<void> {
  if (!(await isPermissionGranted())) {
    return;
  }

  sendNotification({
    title: '下载失败',
    body: message,
  });
}
