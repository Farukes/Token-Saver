//! Token-Saver Core Engine
//! High-performance, zero-latency token optimization library.

pub mod cache;
pub mod config;
pub mod filters;
pub mod models;
pub mod telemetry;
pub mod token_counter;

pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}
