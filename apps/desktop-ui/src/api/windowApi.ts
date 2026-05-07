import { getCurrentWindow } from '@tauri-apps/api/window';
import type { UnlistenFn } from '@tauri-apps/api/event';

const appWindow = getCurrentWindow();

let forceClose = false;
let closeGuard: (() => Promise<boolean>) | null = null;

export function setCloseGuard(guard: (() => Promise<boolean>) | null): void {
  closeGuard = guard;
}

export function startWindowDrag(): Promise<void> {
  return appWindow.startDragging();
}

export function minimizeWindow(): Promise<void> {
  return appWindow.minimize();
}

export function toggleMaximizeWindow(): Promise<void> {
  return appWindow.toggleMaximize();
}

export async function requestWindowClose(): Promise<void> {
  if (!(await canClose())) {
    return;
  }

  await closeWindowWithoutGuard();
}

export function registerWindowCloseGuard(): Promise<UnlistenFn> {
  return appWindow.onCloseRequested(async (event) => {
    if (forceClose) {
      forceClose = false;
      return;
    }

    if (!closeGuard) {
      return;
    }

    event.preventDefault();
    if (await canClose()) {
      await closeWindowWithoutGuard();
    }
  });
}

async function canClose(): Promise<boolean> {
  if (!closeGuard) {
    return true;
  }

  return closeGuard();
}

async function closeWindowWithoutGuard(): Promise<void> {
  forceClose = true;
  try {
    await appWindow.close();
  } catch (error) {
    forceClose = false;
    throw error;
  }
}
