#![warn(clippy::all)]
#![allow(clippy::bool_comparison)]

#[cfg(test)]
#[macro_use]
extern crate indexmap;

mod action;
pub mod area_of_study;
mod audit;
mod filter;
mod limit;
pub mod requirement;
mod rules;
mod save;
mod traits;
mod util;

pub use traits::print::Print;
