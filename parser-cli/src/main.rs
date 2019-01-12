use std::env;
use std::fs;

extern crate hanson_parser;
extern crate serde_yaml;

use hanson_parser::area_of_study::AreaOfStudy;

fn main() {
    let args: Vec<String> = env::args().collect();
    let filename = &args[1];

    let contents = fs::read_to_string(filename).expect(&format!(
        "Something went wrong reading the file `{}`",
        filename
    ));

    let area: AreaOfStudy = serde_yaml::from_str(&contents).unwrap();

    println!("{}", serde_yaml::to_string(&area).unwrap());
}
