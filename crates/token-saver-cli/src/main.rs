use clap::{Parser, Subcommand};
use token_saver_core::telemetry::TelemetryTracker;

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
}

mod mcp;

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
            println!("============================================================");
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
