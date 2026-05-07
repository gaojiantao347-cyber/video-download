use serde::Deserialize;
use serde_json::json;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::State;

use crate::engine_process::EngineProcessManager;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct DownloadFile {
    file_path: String,
}

#[tauri::command]
pub fn open_download_file(
    task_id: String,
    engine_process: State<'_, EngineProcessManager>,
) -> Result<(), String> {
    let path = download_file_path(&engine_process, &task_id)?;
    ensure_file(&path)?;
    tauri_plugin_opener::open_path(&path, None::<&str>)
        .map_err(|error| format!("打开下载文件失败: {error}"))
}

#[tauri::command]
pub fn reveal_download_file(
    task_id: String,
    engine_process: State<'_, EngineProcessManager>,
) -> Result<(), String> {
    let path = download_file_path(&engine_process, &task_id)?;
    ensure_file(&path)?;
    tauri_plugin_opener::reveal_item_in_dir(&path)
        .map_err(|error| format!("打开下载目录失败: {error}"))
}

fn download_file_path(
    engine_process: &EngineProcessManager,
    task_id: &str,
) -> Result<PathBuf, String> {
    if task_id.trim().is_empty() {
        return Err("任务 ID 不能为空".to_string());
    }

    let response = engine_process.call(json!({
        "jsonrpc": "2.0",
        "id": next_request_id("download.getFile"),
        "method": "download.getFile",
        "params": {
            "taskId": task_id,
        },
    }))?;

    if let Some(error) = response.get("error") {
        let message = error
            .get("message")
            .and_then(serde_json::Value::as_str)
            .unwrap_or("获取下载文件失败");
        return Err(message.to_string());
    }

    let Some(result) = response.get("result") else {
        return Err("下载引擎未返回文件信息".to_string());
    };
    let file = serde_json::from_value::<DownloadFile>(result.clone())
        .map_err(|error| format!("解析下载文件信息失败: {error}"))?;
    Ok(PathBuf::from(file.file_path))
}

fn ensure_file(path: &PathBuf) -> Result<(), String> {
    if path.is_file() {
        return Ok(());
    }
    Err("文件不存在或已被清理".to_string())
}

fn next_request_id(method: &str) -> String {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .unwrap_or_default();
    format!("tauri-{method}-{timestamp}")
}
