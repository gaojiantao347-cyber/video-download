use serde_json::Value;
use tauri::State;

use crate::engine_process::EngineProcessManager;

#[tauri::command]
pub fn engine_rpc(
    request: Value,
    engine_process: State<'_, EngineProcessManager>,
) -> Result<Value, String> {
    validate_request(&request)?;
    engine_process.call(request)
}

fn validate_request(request: &Value) -> Result<(), String> {
    let Some(jsonrpc) = request.get("jsonrpc").and_then(Value::as_str) else {
        return Err("JSON-RPC 请求缺少 jsonrpc".to_string());
    };
    if jsonrpc != "2.0" {
        return Err("JSON-RPC 版本必须是 2.0".to_string());
    }

    let Some(method) = request.get("method").and_then(Value::as_str) else {
        return Err("JSON-RPC 请求缺少 method".to_string());
    };
    if method.is_empty() {
        return Err("JSON-RPC method 不能为空".to_string());
    }

    let Some(id) = request.get("id").and_then(Value::as_str) else {
        return Err("JSON-RPC 请求缺少 id".to_string());
    };
    if id.is_empty() {
        return Err("JSON-RPC id 不能为空".to_string());
    }

    Ok(())
}
