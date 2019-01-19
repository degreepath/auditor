use std::fmt;

pub type Result = std::result::Result<String, fmt::Error>;

pub trait Print {
	fn print(&self) -> Result;
}
