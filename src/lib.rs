#![warn(clippy::all)]
#![allow(clippy::bool_comparison)]

mod action;
pub mod area_of_study;
mod audit;
mod filter;
mod limit;
pub mod requirement;
mod rules;
mod save;
mod student;
mod traits;
mod util;
mod value;

pub use traits::print::Print;
