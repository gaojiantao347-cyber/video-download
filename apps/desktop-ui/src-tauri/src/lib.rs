mod engine_commands;
mod engine_process;
mod file_commands;
mod rpc_bridge;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            app.manage(engine_process::EngineProcessManager::new(
                app.handle().clone(),
            ));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            engine_commands::engine_restart,
            file_commands::open_download_file,
            file_commands::reveal_download_file,
            rpc_bridge::engine_rpc
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
