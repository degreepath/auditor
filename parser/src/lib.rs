#![warn(clippy::all)]

#[macro_use]
extern crate serde_derive;

#[cfg(test)]
#[macro_use]
extern crate indexmap;

mod action;
pub mod area_of_study;
mod filter;
mod limit;
pub mod requirement;
mod rules;
mod save;
mod traits;
mod util;

pub use traits::print::Print;
