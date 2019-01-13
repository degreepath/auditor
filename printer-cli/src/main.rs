use std::env;
use std::fs;

extern crate degreepath_parser;
extern crate degreepath_printer;
extern crate serde_yaml;

use degreepath_parser::area_of_study::AreaOfStudy;

fn main() {
    let args: Vec<String> = env::args().collect();
    let filename = &args[1];

    let contents = fs::read_to_string(filename)
        .unwrap_or_else(|_| panic!("Something went wrong reading the file `{}`", filename));

    let area: AreaOfStudy = serde_yaml::from_str(&contents).unwrap();

    println!("{}", degreepath_printer::print(area));
}
