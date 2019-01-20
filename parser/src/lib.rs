#![warn(clippy::all)]

#[macro_use]
extern crate serde_derive;

#[cfg(test)]
#[macro_use]
extern crate maplit;

#[cfg(test)]
#[macro_use]
extern crate indexmap;

pub mod area_of_study;
pub mod requirement;
pub mod rules;
pub mod save;
mod surplus;
mod traits;
mod util;

pub use traits::print::Print;
