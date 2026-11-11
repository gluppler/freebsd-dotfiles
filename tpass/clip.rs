// Secrets stay in pipes and the bounded Wayland owner's memory, never argv/files.
use std::io::Write;
use std::process::{Command, Stdio};
use anyhow::{bail, Context, Result};
use super::config;

pub fn clip(data: &str, display_name: &str) -> Result<()> {
    if data.len() > 1024 * 1024 { bail!("Clipboard entry exceeds 1 MiB"); }
    let seconds = config::clip_time();
    if !(1..=3600).contains(&seconds) { bail!("Clipboard expiry must be 1..3600 seconds"); }
    let target = config::x_selection();
    match target.as_str() {
        "clipboard" | "primary" => (),
        _ => bail!("Wayland supports clipboard and primary selections only"),
    }
    let mut child = Command::new("nostromo-secret-copy")
        .args([&seconds.to_string(), &target]).stdin(Stdio::piped())
        .stdout(Stdio::null()).spawn().context("Could not start password clipboard owner")?;
    let result = child.stdin.take().context("Missing clipboard input")?.write_all(data.as_bytes());
    let status = child.wait()?;
    result?;
    if !status.success() { bail!("Could not set Wayland password clipboard"); }
    println!("Copied {}; expires in {} seconds.", display_name, seconds);
    Ok(())
}
