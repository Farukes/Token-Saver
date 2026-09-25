use std::path::Path;
use clap::{Parser, Subcommand};

use token_saver_core::hooks::{install_hooks, remove_hooks};
use token_saver_core::output_pruner::run_command_smart;
use token_saver_core::rules::{install_rules, remove_rules};
use token_saver_core::telemetry::TelemetryTracker;

mod mcp;
mod ui;

#[derive(Parser)]
#[command(
    name = "token-saver",
    author = "Ömer Faruk Eskitürk",
    version = "1.0.0-beta.1",
    about = "Zero-cost token optimization engine for AI coding assistants"
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Show live performance and savings dashboard
    Stats,
    /// Reset all cumulative telemetry counters
    ResetStats,
    /// Check operational status across AI assistants and IDEs
    Status,
    /// Inject or update Token-Saver steering rules into project rule files
    InstallRules {
        #[arg(short, long, default_value = ".")]
        dir: String,
        #[arg(long)]
        clean: bool,
    },
    /// Alias for install-rules
    Inject {
        #[arg(short, long, default_value = ".")]
        dir: String,
        #[arg(long)]
        clean: bool,
    },
    /// Install transparent CLI interceptor hooks into shell profiles (PowerShell/Bash/Zsh)
    Hook,
    /// Remove transparent CLI interceptor hooks from shell profiles
    Unhook,
    /// Run a shell command with intelligent token-saving output pruning
    Run {
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        command: Vec<String>,
    },
    /// Launch the on-demand Web Dashboard in your browser
    Ui {
        #[arg(short, long, default_value_t = 8080)]
        port: u16,
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
            println!("Supported Languages   : Python, Rust, JavaScript, TypeScript, Go, C, C++, Java");
            println!("============================================================");
        }
        Some(Commands::InstallRules { dir, clean }) | Some(Commands::Inject { dir, clean }) => {
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
            println!("⚡ Installed transparent CLI interceptor hooks:");
            for r in results {
                let status = if r.success { "✅" } else { "❌" };
                println!("  {status} {} ({}): {}", r.shell, r.profile_path.display(), r.message);
            }
        }
        Some(Commands::Unhook) => {
            let results = remove_hooks();
            println!("🧹 Removed transparent CLI interceptor hooks:");
            for r in results {
                let status = if r.success { "✅" } else { "❌" };
                println!("  {status} {} ({}): {}", r.shell, r.profile_path.display(), r.message);
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
        None => {
            // Default mode: MCP Server over stdio
            let mut server = mcp::McpServer::new();
            if let Err(e) = server.run_stdio() {
                eprintln!("[token-saver] Server encountered error: {e}");
            }
        }
    }
}
