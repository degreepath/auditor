#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::AreaOfStudy;
use degreepath_parser::requirement::Requirement;
use degreepath_parser::Print;
use std::fmt;
use std::fmt::Write;

extern crate textwrap;

pub fn print(area: AreaOfStudy) -> Result<String, fmt::Error> {
	area.print()
}
