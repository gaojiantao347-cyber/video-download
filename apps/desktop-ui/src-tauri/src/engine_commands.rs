use tauri::State;

use crate::engine_process::EngineProcessManager;

#[tauri::command]
pub fn engine_restart(engine_process: State<'_, EngineProcessManager>) -> Result<(), String> {
    engine_process.restart()
}
