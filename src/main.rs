use std::env;
use std::fs;

extern crate gobbldygook_area_auditor;
extern crate serde_yaml;

use gobbldygook_area_auditor::area_of_study::AreaOfStudy;

fn main() {
    let args: Vec<String> = env::args().collect();
    let filename = &args[1];

    let contents = fs::read_to_string(filename).expect(&format!(
        "Something went wrong reading the file `{}`",
        filename
    ));

    // println!("With text:\n{}", contents);

    let actual: AreaOfStudy = serde_yaml::from_str(&contents).unwrap();

    println!("{}", serde_yaml::to_string(&actual).unwrap());
}
