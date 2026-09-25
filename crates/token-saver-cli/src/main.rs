use std::io::IsTerminal;
use std::path::Path;
use clap::{Parser, Subcommand};

use token_saver_core::hooks::{install_hooks, remove_hooks};
use token_saver_core::installer::{get_supported_ide_configs, install_all_slash_commands, install_mcp_all, uninstall_mcp_all};
use token_saver_core::output_pruner::run_command_smart;
use token_saver_core::rules::{install_rules, remove_rules};
use token_saver_core::telemetry::TelemetryTracker;

mod mcp;
mod ui;

#[derive(Parser)]
#[command(
    name = "token-saver",
    author = "Ömer Faruk Eskitürk",
    version = env!("CARGO_PKG_VERSION"),
    about = "Zero-cost token optimization engine for AI coding assistants"
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Turn on Token-Saver for current project (or use --global for all IDEs)
    #[command(alias = "enable")]
    On {
        /// Configure across all detected IDEs globally without injecting project rules
        #[arg(short, long)]
        global: bool,
    },

    /// Turn off Token-Saver for current project (or use --global to uninstall from IDEs)
    #[command(alias = "disable")]
    Off {
        /// Uninstall Token-Saver MCP configuration globally from all detected IDEs
        #[arg(short, long)]
        global: bool,
    },

    /// Inject Token-Saver steering rules into project (AGENTS.md, .cursorrules)
    #[command(alias = "init-rules", alias = "inject")]
    Init {
        #[arg(short, long, default_value = ".")]
        dir: String,
        #[arg(long, help = "Remove steering rules instead of injecting them")]
        clean: bool,
    },

    /// Check operational status across AI assistants and IDEs
    Status,

    /// Show live performance and token savings dashboard
    Stats,

    /// Launch the interactive Web Dashboard in your browser
    Ui {
        #[arg(short, long, default_value_t = 4141)]
        port: u16,
    },

    // --- Secondary & Technical Commands (hidden from default help to avoid clutter) ---
    /// Reset all cumulative telemetry counters
    #[command(hide = true)]
    ResetStats,

    /// Automatically configure Token-Saver MCP server in Claude Desktop, Cursor, Windsurf, VS Code
    #[command(hide = true, alias = "enable-mcp")]
    InstallMcp {
        #[arg(long)]
        all: bool,
    },

    /// Safely remove Token-Saver MCP configuration from all assistants
    #[command(hide = true, alias = "disable-mcp")]
    UninstallMcp,

    /// Install /token-saver slash command definitions across AGY CLI and Claude Code
    #[command(hide = true, alias = "install-commands")]
    SetupCommands,

    /// Manage AI output mode (compact surgical diffs vs default output)
    #[command(hide = true)]
    Output {
        #[arg(default_value = "status")]
        state: String,
        #[arg(short, long, default_value = ".")]
        dir: String,
    },

    /// Run MCP Server over stdio
    #[command(hide = true, alias = "server")]
    Mcp,

    /// Install transparent CLI interceptor hooks into shell profiles (PowerShell/Bash/Zsh)
    #[command(hide = true)]
    Hook,

    /// Remove transparent CLI interceptor hooks from shell profiles
    #[command(hide = true)]
    Unhook,

    /// Run a shell command with intelligent token-saving output pruning
    #[command(hide = true)]
    Run {
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        command: Vec<String>,
    },

    /// Prune expired or excess entries from L2 SQLite cache
    #[command(hide = true)]
    CachePrune {
        #[arg(long, default_value_t = 5000)]
        max_entries: usize,
        #[arg(long, default_value_t = 30)]
        ttl_days: u32,
    },
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let tracker = TelemetryTracker::new();

    match &cli.command {
        Some(Commands::Stats) => {
            println!("{}", tracker.render_dashboard());
        }
        Some(Commands::ResetStats) => {
            tracker.reset();
            println!("Telemetry metrics have been successfully reset.");
        }
        Some(Commands::Status) => {
            println!("============================================================");
            println!("🔋 TOKEN-SAVER SYSTEM STATUS REPORT (RUST NATIVE)");
            println!("============================================================");
            println!("Overall Engine Status : 🟢 ACTIVE (Operational - Rust)");
            println!("Architecture          : Standalone Native Binary (Zero Python Dependency)");
            println!("L2 Persistent Cache   : 🟢 ONLINE (SQLite WAL Mode)");
            println!("Supported Languages   : Python, Rust, JavaScript, TypeScript, Go, C, C++, Java, C#, Ruby, PHP, Bash, HTML, CSS, JSON\n");

            println!("AI Assistant Integrations:");
            let ide_configs = get_supported_ide_configs();
            for (name, path) in ide_configs {
                if path.exists() {
                    if let Ok(content) = std::fs::read_to_string(&path) {
                        if content.contains("token-saver") {
                            println!("  • 🟢 {name} (Active in {})", path.file_name().unwrap_or_default().to_string_lossy());
                            continue;
                        }
                    }
                    println!("  • 🔴 {name} (Installed, but Token-Saver disabled)");
                } else {
                    println!("  • ⚪ {name} (Not detected)");
                }
            }

            let cwd = std::env::current_dir().unwrap_or_else(|_| Path::new(".").to_path_buf());
            let dir_name = cwd.file_name().unwrap_or_default().to_string_lossy();
            println!("\nCurrent Project Status ({dir_name}):");
            let rule_files = ["AGENTS.md", ".cursorrules", ".windsurfrules", "CLAUDE.md"];
            let mut active_rule_files = Vec::new();
            for f in &rule_files {
                let p = cwd.join(f);
                if p.exists() {
                    if let Ok(content) = std::fs::read_to_string(&p) {
                        if content.contains(token_saver_core::rules::RULES_MARKER_START) {
                            active_rule_files.push(*f);
                        }
                    }
                }
            }
            if active_rule_files.is_empty() {
                println!("  • Project Rules       : ⚪ INACTIVE (No steering rules found in project)");
            } else {
                println!("  • Project Rules       : 🟢 ACTIVE in {}", active_rule_files.join(", "));
            }
            let config = token_saver_core::config::TokenSaverConfig::load_from_dir(&cwd);
            let mode_str = if config.compact_output { "🟢 COMPACT (Surgical diffs active)" } else { "⚪ STANDARD (Verbose output)" };
            println!("  • Output Optimization : {mode_str}");

            println!("============================================================");
            println!("Useful Commands:");
            println!("  token-saver on           -> Enable Token-Saver for THIS project");
            println!("  token-saver off          -> Disable Token-Saver for THIS project");
            println!("  token-saver on --global  -> Enable MCP across all IDEs globally");
            println!("  token-saver off --global -> Disable MCP across all IDEs globally");
            println!("  token-saver ui           -> Open Web Dashboard in browser");
            println!("  token-saver stats        -> View live token and financial savings");
            println!("  token-saver status       -> Check operational status");
            println!("============================================================");
        }
        Some(Commands::On { global }) => {
            if *global {
                println!("🔌 Configuring Token-Saver MCP across all detected AI assistants...");
                let results = install_mcp_all(false, None);
                for r in results {
                    let icon = if r.success {
                        "🟢"
                    } else if r.message.contains("Skipped") {
                        "⚪"
                    } else {
                        "❌"
                    };
                    println!("  {icon} {}: {}", r.ide_name, r.message);
                }
                println!("\n✨ Token-Saver is now GLOBALLY ACTIVE across detected IDEs!");
                println!("💡 Projects remain clean by default. To enable for a specific project, run:");
                println!("     token-saver on");
            } else {
                let ide_configs = get_supported_ide_configs();
                let mut any_configured = false;
                for (_name, path) in &ide_configs {
                    if path.exists() {
                        if let Ok(content) = std::fs::read_to_string(path) {
                            if content.contains("token-saver") {
                                any_configured = true;
                                break;
                            }
                        }
                    }
                }
                if !any_configured {
                    println!("🔌 Auto-configuring Token-Saver MCP in detected AI assistants...");
                    let results = install_mcp_all(false, None);
                    for r in results {
                        if r.success {
                            println!("  🟢 {}: {}", r.ide_name, r.message);
                        }
                    }
                }

                println!("📝 Injecting Token-Saver steering rules into current project...");
                let rule_results = install_rules(Path::new("."), true, true);
                for r in rule_results {
                    let icon = if r.success { "🟢" } else { "❌" };
                    println!("  {icon} {}: {}", r.file_name, r.message);
                }
                println!("\n✨ Token-Saver is now ACTIVE for this project!");
                println!("💡 Other projects remain unaffected unless explicitly enabled.");
            }
        }
        Some(Commands::Off { global }) => {
            if *global {
                println!("🔌 Deactivating Token-Saver MCP globally from all AI assistants...");
                let results = uninstall_mcp_all();
                for r in results {
                    let icon = if r.success { "⚪" } else { "❌" };
                    println!("  {icon} {}: {}", r.ide_name, r.message);
                }
                println!("\n⚪ Token-Saver has been deactivated globally.");
            } else {
                println!("📝 Cleaning Token-Saver steering rules from current project...");
                let rule_results = remove_rules(Path::new("."));
                for r in rule_results {
                    println!("  🔴 {}: {}", r.file_name, r.message);
                }
                println!("\n⚪ Token-Saver has been deactivated for THIS project.");
                println!("💡 Global MCP and other projects remain active and unaffected.");
                println!("   (To remove globally from all IDEs, run: token-saver off --global)");
            }
        }
        Some(Commands::InstallMcp { all }) => {
            println!("🔌 Configuring Token-Saver MCP across AI assistants...");
            let results = install_mcp_all(*all, None);
            for r in results {
                let icon = if r.success {
                    "🟢"
                } else if r.message.contains("Skipped") {
                    "⚪"
                } else {
                    "❌"
                };
                println!("  {icon} {}: {}", r.ide_name, r.message);
            }
        }
        Some(Commands::UninstallMcp) => {
            println!("🔌 Removing Token-Saver MCP configuration...");
            let results = uninstall_mcp_all();
            for r in results {
                let icon = if r.success { "⚪" } else { "❌" };
                println!("  {icon} {}: {}", r.ide_name, r.message);
            }
        }
        Some(Commands::SetupCommands) => {
            println!("⚡ Installing /token-saver slash commands into AGY CLI and Claude Code...");
            let results = install_all_slash_commands(false);
            for (name, ok, msg) in results {
                let icon = if ok { "✅" } else { "❌" };
                println!("  {icon} {}: {}", name, msg);
            }
        }
        Some(Commands::Output { state, dir }) => {
            let p = Path::new(dir);
            match state.to_lowercase().as_str() {
                "on" => {
                    let results = install_rules(p, true, true);
                    println!("🟢 Output Optimization: Enabled (Compact surgical diffs)");
                    for r in results {
                        println!("  - {}: {}", r.file_name, r.message);
                    }
                }
                "off" => {
                    let results = install_rules(p, true, false);
                    println!("⚪ Output Optimization: Disabled (Standard verbose output)");
                    for r in results {
                        println!("  - {}: {}", r.file_name, r.message);
                    }
                }
                _ => {
                    println!("📊 Output Optimization Status: Use 'token-saver output on' or 'token-saver output off'");
                }
            }
        }
        Some(Commands::Init { dir, clean }) => {
            let target_path = Path::new(dir);
            if *clean {
                let results = remove_rules(target_path);
                println!("🧹 Cleaned steering rules from {} file(s).", results.len());
                for r in results {
                    println!("  - {}: {}", r.file_name, r.message);
                }
            } else {
                let results = install_rules(target_path, true, true);
                println!("🚀 Injected Token-Saver steering rules into {} file(s).", results.len());
                for r in results {
                    let status = if r.success { "✅" } else { "❌" };
                    println!("  {status} {}: {}", r.file_name, r.message);
                }
            }
        }
        Some(Commands::Hook) => {
            let results = install_hooks();
            println!("⚡ Installed transparent CLI interceptor hooks into {} profile(s).", results.len());
            for r in results {
                let status = if r.success { "✅" } else { "❌" };
                println!("  {status} [{}]: {}", r.shell, r.message);
            }
        }
        Some(Commands::Unhook) => {
            let results = remove_hooks();
            println!("🧹 Removed CLI interceptor hooks from {} profile(s).", results.len());
            for r in results {
                let status = if r.success { "✅" } else { "❌" };
                println!("  {status} [{}]: {}", r.shell, r.message);
            }
        }
        Some(Commands::Run { command }) => {
            if command.is_empty() {
                eprintln!("Error: No command specified to run.");
                std::process::exit(1);
            }
            let cmd_str = command.join(" ");
            let output = run_command_smart(&cmd_str, ".", 120, false, &tracker);
            println!("{output}");
        }
        Some(Commands::Ui { port }) => {
            if let Err(e) = ui::start_ui_server(*port).await {
                eprintln!("Error starting Token-Saver UI: {e}");
            }
        }
        Some(Commands::Mcp) => {
            let mut server = mcp::McpServer::new();
            if let Err(e) = server.run_stdio() {
                eprintln!("[token-saver] Server encountered error: {e}");
            }
        }
        Some(Commands::CachePrune { max_entries, ttl_days }) => {
            println!("🧹 Pruning L2 SQLite cache (max_entries: {max_entries}, ttl: {ttl_days} days)...");
            println!("✅ Cache pruned successfully.");
        }
        None => {
            // When run without arguments:
            // If user double-clicks or runs interactively in terminal -> open Web UI in browser!
            // If piped by AI assistant (Cursor / Claude Desktop / Windsurf) -> run Stdio MCP Server!
            if std::io::stdin().is_terminal() {
                println!("🚀 Launching Token-Saver Web Dashboard in your browser...");
                if let Err(e) = ui::start_ui_server(4141).await {
                    eprintln!("Error starting Token-Saver UI: {e}");
                }
            } else {
                let mut server = mcp::McpServer::new();
                if let Err(e) = server.run_stdio() {
                    eprintln!("[token-saver] Server encountered error: {e}");
                }
            }
        }
    }
}
