use std::env;
use std::fs;

extern crate degreepath_auditor;
extern crate serde_json;
extern crate serde_yaml;

use degreepath_auditor::area_of_study::AreaOfStudy;
use degreepath_auditor::student::StudentData;
use rayon::prelude::*;

fn main() {
	let args: Vec<String> = env::args().skip(1).collect();
	let student_filename = &args[0];
	let area_names: Vec<_> = args.iter().skip(1).collect();

	let student_contents = fs::read_to_string(student_filename)
		.unwrap_or_else(|_| panic!("Something went wrong reading the file `{}`", student_filename));

	eprintln!("student file read: {}", student_filename);

	let student: StudentData = serde_yaml::from_str(&student_contents).unwrap();

	eprintln!("student file processed");

	let area_contentses: Vec<AreaOfStudy> = area_names
		.par_iter()
		.filter_map(|filename| fs::read_to_string(filename).ok())
		.filter_map(|contents| serde_yaml::from_str::<AreaOfStudy>(&contents).ok())
		.collect();

	eprintln!(
		"areas read and processed: {:?}",
		area_contentses.iter().map(|a| a.area_name.clone()).collect::<Vec<_>>()
	);

	let loaded_areas: Vec<AreaOfStudy> = student
		.areas
		.par_iter()
		.map(|descriptor| {
			let name = descriptor.get("name").and_then(|v| v.to_string()).unwrap();
			let kind = descriptor.get("type").and_then(|v| v.to_string()).unwrap();
			let catalog = descriptor.get("catalog").and_then(|v| v.to_string()).unwrap();

			let area = area_contentses
				.iter()
				.find(|area| area.area_name == name && area.area_type.to_string() == kind && area.catalog == catalog)
				.expect(&format!("an area matching {}, {}, {}", name, kind, catalog));

			area.clone()
		})
		.collect();

	eprintln!("areas matched; beginning audit");

	loaded_areas.par_iter().for_each(|area| {
		println!("starting {}", area.area_name);
		let result = area.check(&student);
		println!("completed {}", area.area_name);
		println!("{:#?}", result);
	});

	eprintln!("audit complete");

	// println!("{}", serde_json::to_string_pretty(&student).unwrap());
	// println!("{:#?}", student);
}
