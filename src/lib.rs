#![warn(clippy::all)]

#[macro_use]
extern crate serde_derive;
extern crate serde_yaml;

pub mod area_of_study;
mod requirement;
mod rules;
mod save;
mod util;

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
