use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{path::BaseDirectory, AppHandle, Manager};

const PYTHON_ENGINE_PATH_ENV: &str = "PYTHON_ENGINE_PATH";
const SETTINGS_FILE_NAME: &str = "settings.json";
const ENGINE_VERSION: &str = "python-yt-dlp-bridge-0.1.0";

pub struct EngineProcessManager {
    app: AppHandle,
    settings: Mutex<AppSettings>,
    tasks: Arc<Mutex<HashMap<String, DownloadTask>>>,
    sequence: AtomicU64,
}

impl EngineProcessManager {
    pub fn new(app: AppHandle) -> Self {
        let settings = load_settings(&app).unwrap_or_else(|error| {
            eprintln!("[download-engine] 读取设置失败，使用默认设置: {error}");
            AppSettings::default()
        });

        Self {
            app,
            settings: Mutex::new(settings),
            tasks: Arc::new(Mutex::new(HashMap::new())),
            sequence: AtomicU64::new(0),
        }
    }

    pub fn call(&self, request: Value) -> Result<Value, String> {
        let id = request.get("id").cloned().unwrap_or(Value::Null);
        let method = request.get("method").and_then(Value::as_str).unwrap_or("");

        let result = match method {
            "engine.healthCheck" => self.health_check(),
            "engine.getVersion" => Ok(json!({ "version": ENGINE_VERSION })),
            "settings.get" => self.get_settings(),
            "settings.update" => self.update_settings(&request),
            "download.createTask" => self.create_download_task(&request),
            "download.getTask" => self.get_download_task(&request),
            "download.getFile" => self.get_download_file(&request),
            _ => Err(rpc_failure(
                "RPC_METHOD_NOT_FOUND",
                "当前下载引擎暂不支持该方法",
            )),
        };

        Ok(match result {
            Ok(payload) => json!({
                "jsonrpc": "2.0",
                "id": id,
                "result": payload,
            }),
            Err(error) => json!({
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": error.code,
                    "message": error.message,
                },
            }),
        })
    }

    pub fn restart(&self) -> Result<(), String> {
        let settings = load_settings(&self.app).unwrap_or_default();
        let mut guard = self
            .settings
            .lock()
            .map_err(|_| "下载引擎设置锁已损坏".to_string())?;
        *guard = settings;
        Ok(())
    }

    fn health_check(&self) -> Result<Value, RpcFailure> {
        Ok(json!({
            "version": ENGINE_VERSION,
            "status": "RUNNING",
            "taskStore": "IN_MEMORY",
        }))
    }

    fn get_settings(&self) -> Result<Value, RpcFailure> {
        let settings = self
            .settings
            .lock()
            .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "读取设置失败"))?
            .clone();
        Ok(json!(settings))
    }

    fn update_settings(&self, request: &Value) -> Result<Value, RpcFailure> {
        let settings = request_params::<AppSettings>(request)?;
        validate_settings(&settings)?;
        save_settings(&self.app, &settings).map_err(|error| rpc_failure("STORAGE_ERROR", error))?;

        let mut guard = self
            .settings
            .lock()
            .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "保存设置失败"))?;
        *guard = settings.clone();

        Ok(json!(settings))
    }

    fn create_download_task(&self, request: &Value) -> Result<Value, RpcFailure> {
        let params = request_params::<CreateDownloadTaskParams>(request)?;
        let url = validate_url(&params.url)?;
        let output_dir = self.resolve_output_dir(params.output_dir.as_deref())?;
        ensure_download_dir(&output_dir)?;

        let task_id = self.next_task_id();
        let now = now_iso_string();
        let task = DownloadTask {
            task_id: task_id.clone(),
            source_url: url.clone(),
            platform: detect_platform(&url),
            title: None,
            author: None,
            cover_url: None,
            remove_watermark: params.remove_watermark,
            watermark_status: if params.remove_watermark {
                "UNAVAILABLE".to_string()
            } else {
                "NOT_REQUESTED".to_string()
            },
            status: "PENDING".to_string(),
            progress: 0,
            file_name: None,
            file_path: None,
            error_code: None,
            error_message: None,
            created_at: now.clone(),
            updated_at: now,
        };

        let mut command = resolve_python_engine_command(&self.app)
            .map_err(|error| rpc_failure("RPC_INTERNAL_ERROR", error))?;
        append_download_args(&mut command, &task_id, &url, &output_dir, &params);

        let mut child = command
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|error| {
                rpc_failure(
                    "RPC_INTERNAL_ERROR",
                    format!(
                        "启动 Python 下载引擎失败: {error}。{}",
                        python_engine_setup_hint()
                    ),
                )
            })?;

        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| rpc_failure("RPC_INTERNAL_ERROR", "无法读取 Python 下载引擎 stdout"))?;
        if let Some(stderr) = child.stderr.take() {
            drain_stderr(stderr);
        }

        {
            let mut tasks = self
                .tasks
                .lock()
                .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "下载任务表锁已损坏"))?;
            tasks.insert(task_id.clone(), task);
        }

        update_task(&self.tasks, &task_id, |task| {
            task.status = "DOWNLOADING".to_string();
            task.updated_at = now_iso_string();
        });

        let tasks = Arc::clone(&self.tasks);
        let thread_task_id = task_id.clone();
        thread::spawn(move || {
            watch_download_process(tasks, thread_task_id, stdout, child);
        });

        Ok(json!({
            "taskId": task_id,
            "status": "PENDING",
            "removeWatermark": params.remove_watermark,
        }))
    }

    fn get_download_task(&self, request: &Value) -> Result<Value, RpcFailure> {
        let params = request_params::<TaskIdParams>(request)?;
        let tasks = self
            .tasks
            .lock()
            .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "下载任务表锁已损坏"))?;
        let task = tasks
            .get(&params.task_id)
            .ok_or_else(|| rpc_failure("TASK_NOT_FOUND", "下载任务不存在"))?;
        Ok(json!(task))
    }

    fn get_download_file(&self, request: &Value) -> Result<Value, RpcFailure> {
        let params = request_params::<TaskIdParams>(request)?;
        let tasks = self
            .tasks
            .lock()
            .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "下载任务表锁已损坏"))?;
        let task = tasks
            .get(&params.task_id)
            .ok_or_else(|| rpc_failure("TASK_NOT_FOUND", "下载任务不存在"))?;

        if task.status != "SUCCESS" {
            return Err(rpc_failure("FILE_NOT_READY", "文件尚未下载完成"));
        }

        let file_path = task
            .file_path
            .as_ref()
            .ok_or_else(|| rpc_failure("FILE_NOT_FOUND", "下载文件路径缺失"))?;
        let path = PathBuf::from(file_path);
        if !path.is_file() {
            return Err(rpc_failure("FILE_NOT_FOUND", "文件不存在或已被清理"));
        }

        Ok(json!({
            "taskId": task.task_id.clone(),
            "fileName": task.file_name.clone().unwrap_or_else(|| file_name_from_path(&path)),
            "filePath": file_path,
        }))
    }

    fn resolve_output_dir(&self, request_output_dir: Option<&str>) -> Result<PathBuf, RpcFailure> {
        if let Some(output_dir) = request_output_dir.filter(|value| !value.trim().is_empty()) {
            return Ok(PathBuf::from(output_dir));
        }

        let settings = self
            .settings
            .lock()
            .map_err(|_| rpc_failure("RPC_INTERNAL_ERROR", "读取下载目录失败"))?;
        if settings.download_dir.trim().is_empty() {
            return Err(rpc_failure("STORAGE_ERROR", "请先设置下载目录"));
        }

        Ok(PathBuf::from(&settings.download_dir))
    }

    fn next_task_id(&self) -> String {
        let sequence = self.sequence.fetch_add(1, Ordering::Relaxed) + 1;
        format!("task-{}-{sequence}", now_millis())
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct AppSettings {
    download_dir: String,
    max_concurrent_downloads: u8,
    remove_watermark: bool,
    allow_fallback: bool,
    enable_system_notifications: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            download_dir: String::new(),
            max_concurrent_downloads: 2,
            remove_watermark: true,
            allow_fallback: true,
            enable_system_notifications: false,
        }
    }
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct DownloadTask {
    task_id: String,
    source_url: String,
    platform: Option<String>,
    title: Option<String>,
    author: Option<String>,
    cover_url: Option<String>,
    remove_watermark: bool,
    watermark_status: String,
    status: String,
    progress: u8,
    file_name: Option<String>,
    file_path: Option<String>,
    error_code: Option<String>,
    error_message: Option<String>,
    created_at: String,
    updated_at: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct CreateDownloadTaskParams {
    url: String,
    remove_watermark: bool,
    allow_fallback: bool,
    #[serde(default)]
    output_dir: Option<String>,
    #[serde(default)]
    cookies_file: Option<String>,
    #[serde(default)]
    cookies_from_browser: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct TaskIdParams {
    task_id: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PythonEvent {
    #[serde(rename = "type")]
    event_type: String,
    request_id: String,
    #[serde(default)]
    status: Option<String>,
    #[serde(default)]
    percent: Option<f64>,
    #[serde(default)]
    file_name: Option<String>,
    #[serde(default)]
    file_path: Option<String>,
    #[serde(default)]
    title: Option<String>,
    #[serde(default)]
    error_code: Option<String>,
    #[serde(default)]
    message: Option<String>,
}

#[derive(Debug)]
struct RpcFailure {
    code: String,
    message: String,
}

fn rpc_failure(code: impl Into<String>, message: impl Into<String>) -> RpcFailure {
    RpcFailure {
        code: code.into(),
        message: message.into(),
    }
}

fn request_params<T>(request: &Value) -> Result<T, RpcFailure>
where
    T: DeserializeOwned,
{
    let params = request.get("params").cloned().unwrap_or_else(|| json!({}));
    serde_json::from_value(params).map_err(|error| {
        rpc_failure(
            "RPC_INVALID_REQUEST",
            format!("JSON-RPC 参数格式不正确: {error}"),
        )
    })
}

fn validate_settings(settings: &AppSettings) -> Result<(), RpcFailure> {
    if settings.download_dir.trim().is_empty() {
        return Err(rpc_failure("RPC_INVALID_REQUEST", "下载目录不能为空"));
    }
    if settings.max_concurrent_downloads < 1 || settings.max_concurrent_downloads > 4 {
        return Err(rpc_failure(
            "RPC_INVALID_REQUEST",
            "并发限制必须是 1-4 之间的整数",
        ));
    }

    ensure_download_dir(&PathBuf::from(&settings.download_dir))
}

fn validate_url(url: &str) -> Result<String, RpcFailure> {
    let normalized = url.trim();
    if normalized.is_empty() {
        return Err(rpc_failure("URL_EMPTY", "链接不能为空"));
    }
    if !normalized.starts_with("http://") && !normalized.starts_with("https://") {
        return Err(rpc_failure("URL_INVALID", "链接必须是有效的 HTTP(S) 地址"));
    }
    Ok(normalized.to_string())
}

fn ensure_download_dir(path: &Path) -> Result<(), RpcFailure> {
    fs::create_dir_all(path)
        .map_err(|error| rpc_failure("STORAGE_ERROR", format!("下载目录不可用: {error}")))?;
    if !path.is_dir() {
        return Err(rpc_failure("STORAGE_ERROR", "下载目录不是文件夹"));
    }
    Ok(())
}

fn load_settings(app: &AppHandle) -> Result<AppSettings, String> {
    let path = settings_path(app)?;
    if !path.is_file() {
        return Ok(AppSettings::default());
    }

    let content =
        fs::read_to_string(&path).map_err(|error| format!("读取设置文件失败: {error}"))?;
    serde_json::from_str(&content).map_err(|error| format!("解析设置文件失败: {error}"))
}

fn save_settings(app: &AppHandle, settings: &AppSettings) -> Result<(), String> {
    let path = settings_path(app)?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| format!("创建设置目录失败: {error}"))?;
    }

    let content = serde_json::to_string_pretty(settings)
        .map_err(|error| format!("序列化设置失败: {error}"))?;
    fs::write(path, content).map_err(|error| format!("写入设置文件失败: {error}"))
}

fn settings_path(app: &AppHandle) -> Result<PathBuf, String> {
    app.path()
        .app_config_dir()
        .map(|path| path.join(SETTINGS_FILE_NAME))
        .map_err(|error| format!("解析设置目录失败: {error}"))
}

fn resolve_python_engine_command(app: &AppHandle) -> Result<Command, String> {
    if let Some(path) = env::var_os(PYTHON_ENGINE_PATH_ENV) {
        let path = PathBuf::from(path);
        if path.is_file() {
            return Ok(Command::new(path));
        }
        return Err(format!(
            "{PYTHON_ENGINE_PATH_ENV} 指向的 Python 下载引擎不存在: {}。请检查环境变量，或取消该变量后使用打包内置 vd-engine。",
            path.display()
        ));
    }

    if let Some(command) = packaged_python_engine_command(app)? {
        return Ok(command);
    }

    dev_python_engine_command()
}

fn packaged_python_engine_command(app: &AppHandle) -> Result<Option<Command>, String> {
    let binaries_dir = app
        .path()
        .resolve("binaries", BaseDirectory::Resource)
        .map_err(|error| format!("解析打包引擎资源目录失败: {error}"))?;
    if !binaries_dir.is_dir() {
        return Ok(None);
    }

    let engine = binaries_dir.join(if cfg!(windows) {
        "vd-engine.exe"
    } else {
        "vd-engine"
    });
    if engine.is_file() {
        return Ok(Some(Command::new(engine)));
    }

    if cfg!(debug_assertions) {
        return Ok(None);
    }

    Err(format!(
        "安装包缺少 Python 下载引擎 sidecar: {}。安装包可能损坏，请重新安装；开发调试请先运行 scripts\\build-python-engine.ps1。",
        engine.display()
    ))
}

fn python_engine_setup_hint() -> &'static str {
    if cfg!(debug_assertions) {
        "开发调试请运行 scripts\\build-python-engine.ps1，或设置 PYTHON_ENGINE_PATH 指向 vd-engine.exe。"
    } else {
        "请重新安装应用；如在开发调试，请运行 scripts\\build-python-engine.ps1，或设置 PYTHON_ENGINE_PATH。"
    }
}

fn dev_python_engine_command() -> Result<Command, String> {
    let engine_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .join("engine-python");
    let source_dir = engine_dir.join("src");
    if !source_dir.is_dir() {
        return Err(format!(
            "未找到 Python 下载引擎源码目录: {}。开发调试请确认项目根目录完整，或运行 scripts\\build-python-engine.ps1 后设置 {PYTHON_ENGINE_PATH_ENV} 指向 vd-engine.exe。",
            source_dir.display()
        ));
    }

    let executable = if cfg!(windows) { "python" } else { "python3" };
    let mut command = Command::new(executable);
    command
        .arg("-m")
        .arg("video_download_engine.cli")
        .current_dir(engine_dir)
        .env("PYTHONPATH", source_dir);
    Ok(command)
}

fn append_download_args(
    command: &mut Command,
    task_id: &str,
    url: &str,
    output_dir: &Path,
    params: &CreateDownloadTaskParams,
) {
    command
        .arg("download")
        .arg("--request-id")
        .arg(task_id)
        .arg("--url")
        .arg(url)
        .arg("--output-dir")
        .arg(output_dir);

    command.arg(if params.remove_watermark {
        "--remove-watermark"
    } else {
        "--no-remove-watermark"
    });
    command.arg(if params.allow_fallback {
        "--allow-fallback"
    } else {
        "--no-allow-fallback"
    });

    if let Some(cookies_file) = params
        .cookies_file
        .as_deref()
        .filter(|value| !value.trim().is_empty())
    {
        command.arg("--cookies-file").arg(cookies_file);
    } else if let Some(cookies_from_browser) = params
        .cookies_from_browser
        .as_deref()
        .filter(|value| !value.trim().is_empty())
    {
        command.arg("--cookies-from-browser").arg(cookies_from_browser);
    }
}

fn watch_download_process(
    tasks: Arc<Mutex<HashMap<String, DownloadTask>>>,
    task_id: String,
    stdout: impl std::io::Read,
    mut child: std::process::Child,
) {
    let mut terminal_seen = false;
    let reader = BufReader::new(stdout);

    for line_result in reader.lines() {
        match line_result {
            Ok(line) if line.trim().is_empty() => continue,
            Ok(line) => match serde_json::from_str::<PythonEvent>(&line) {
                Ok(event) => {
                    if event.request_id != task_id {
                        eprintln!(
                            "[download-engine] 忽略 requestId 不匹配的事件: expected={}, actual={}",
                            task_id, event.request_id
                        );
                        continue;
                    }
                    terminal_seen |= handle_python_event(&tasks, &task_id, event);
                }
                Err(error) => {
                    eprintln!("[download-engine] 忽略非 JSON 下载事件: {error}; 原始内容: {line}")
                }
            },
            Err(error) => {
                fail_task(
                    &tasks,
                    &task_id,
                    "DOWNLOAD_FAILED",
                    format!("读取下载进度失败: {error}"),
                );
                terminal_seen = true;
                break;
            }
        }
    }

    let exit_status = child.wait();
    if !terminal_seen {
        let message = match exit_status {
            Ok(status) => format!("Python 下载引擎异常退出: {status}"),
            Err(error) => format!("等待 Python 下载引擎退出失败: {error}"),
        };
        fail_task(&tasks, &task_id, "DOWNLOAD_FAILED", message);
    }
}

fn handle_python_event(
    tasks: &Arc<Mutex<HashMap<String, DownloadTask>>>,
    task_id: &str,
    event: PythonEvent,
) -> bool {
    match event.event_type.as_str() {
        "progress" => {
            update_task(tasks, task_id, |task| {
                task.status = "DOWNLOADING".to_string();
                if let Some(percent) = event.percent {
                    task.progress = clamp_percent(percent);
                } else if event.status.as_deref() == Some("finished") {
                    task.progress = 100;
                }
                if let Some(file_name) = event.file_name {
                    task.file_name = Some(file_name);
                }
                task.updated_at = now_iso_string();
            });
            false
        }
        "completed" => {
            update_task(tasks, task_id, |task| {
                task.status = "SUCCESS".to_string();
                task.progress = 100;
                task.file_path = event.file_path.clone();
                task.file_name = event
                    .file_name
                    .or_else(|| event.file_path.as_deref().map(file_name_from_str));
                task.title = event.title;
                task.error_code = None;
                task.error_message = None;
                task.updated_at = now_iso_string();
            });
            true
        }
        "failed" => {
            fail_task(
                tasks,
                task_id,
                map_python_error_code(event.error_code.as_deref()),
                event.message.unwrap_or_else(|| "下载失败".to_string()),
            );
            true
        }
        _ => {
            eprintln!(
                "[download-engine] 忽略未知下载事件类型: {}",
                event.event_type
            );
            false
        }
    }
}

fn update_task(
    tasks: &Arc<Mutex<HashMap<String, DownloadTask>>>,
    task_id: &str,
    update: impl FnOnce(&mut DownloadTask),
) {
    let Ok(mut guard) = tasks.lock() else {
        eprintln!("[download-engine] 下载任务表锁已损坏");
        return;
    };

    if let Some(task) = guard.get_mut(task_id) {
        update(task);
    }
}

fn fail_task(
    tasks: &Arc<Mutex<HashMap<String, DownloadTask>>>,
    task_id: &str,
    code: impl Into<String>,
    message: impl Into<String>,
) {
    let code = code.into();
    let message = message.into();
    update_task(tasks, task_id, |task| {
        task.status = "FAILED".to_string();
        task.error_code = Some(code);
        task.error_message = Some(message);
        task.updated_at = now_iso_string();
    });
}

fn drain_stderr(stderr: impl std::io::Read + Send + 'static) {
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line_result in reader.lines() {
            match line_result {
                Ok(line) if line.trim().is_empty() => {}
                Ok(line) => eprintln!("[vd-engine] {line}"),
                Err(_) => break,
            }
        }
    });
}

fn map_python_error_code(code: Option<&str>) -> &'static str {
    match code {
        Some("URL_EMPTY") => "URL_EMPTY",
        Some("URL_INVALID") => "URL_INVALID",
        Some("OUTPUT_DIR_INVALID") => "STORAGE_ERROR",
        Some("COOKIES_FILE_INVALID") => "DOWNLOAD_FAILED",
        Some("DOWNLOAD_FAILED") => "DOWNLOAD_FAILED",
        _ => "DOWNLOAD_FAILED",
    }
}

fn detect_platform(url: &str) -> Option<String> {
    let lower = url.to_ascii_lowercase();
    if lower.contains("douyin") || lower.contains("iesdouyin") {
        return Some("DOUYIN".to_string());
    }
    if lower.contains("kuaishou") || lower.contains("kwai") {
        return Some("KUAISHOU".to_string());
    }
    None
}

fn clamp_percent(percent: f64) -> u8 {
    if !percent.is_finite() || percent <= 0.0 {
        return 0;
    }
    if percent >= 100.0 {
        return 100;
    }
    percent.round() as u8
}

fn file_name_from_path(path: &Path) -> String {
    path.file_name()
        .and_then(|value| value.to_str())
        .map(str::to_owned)
        .unwrap_or_else(|| path.display().to_string())
}

fn file_name_from_str(path: &str) -> String {
    file_name_from_path(Path::new(path))
}

fn now_millis() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .unwrap_or_default()
}

fn now_iso_string() -> String {
    let duration = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let total_seconds = duration.as_secs() as i64;
    let millis = duration.subsec_millis();
    let days = total_seconds.div_euclid(86_400);
    let seconds_of_day = total_seconds.rem_euclid(86_400);
    let (year, month, day) = civil_from_days(days);
    let hour = seconds_of_day / 3_600;
    let minute = (seconds_of_day % 3_600) / 60;
    let second = seconds_of_day % 60;

    format!("{year:04}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}.{millis:03}Z")
}

fn civil_from_days(days: i64) -> (i64, u32, u32) {
    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1_460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = mp + if mp < 10 { 3 } else { -9 };
    let year = y + if month <= 2 { 1 } else { 0 };

    (year, month as u32, day as u32)
}
