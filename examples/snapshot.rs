extern crate degreepath_auditor;
extern crate serde_json;
extern crate serde_yaml;

use degreepath_auditor::area_of_study::AreaOfStudy;
use globwalk::glob;
use rayon::prelude::*;
use std::{env, fs, path::PathBuf, process};

type Result<T> = std::result::Result<T, Box<std::error::Error>>;
type FileInput = (String, PathBuf, PathBuf);

fn convert_file((name, input, output_dir): &FileInput) -> Result<()> {
	let contents = fs::read(&input)?;
	let area: AreaOfStudy = serde_yaml::from_slice(&contents)?;

	let markdown_path = output_dir.clone().with_file_name(format!("{}.md", name));
	let markdown_output = area.print()?;
	fs::write(&markdown_path, markdown_output + "\n")?;

	let json_path = output_dir.clone().with_file_name(format!("{}.json", name));
	let json_output = serde_json::to_string_pretty(&area)?;
	fs::write(&json_path, json_output + "\n")?;

	Ok(())
}

fn process_area_file(entry: &globwalk::DirEntry) -> Result<FileInput> {
	let p = entry.path();
	let components: Vec<_> = p.components().into_iter().collect();
	let catalog = components[2].as_os_str().to_str().expect("valid utf-8");
	let kind = components[3].as_os_str().to_str().expect("valid utf-8");
	let name = p.file_stem().unwrap().to_str().expect("valid utf-8");

	// eprintln!("current: {}, {}, {}", catalog, kind, name);
	let snapshots_dir = PathBuf::from(format!("./snapshots/{}/{}/filename.out", catalog, kind));
	fs::create_dir_all(&snapshots_dir)?;

	Ok((String::from(name), PathBuf::from(p), snapshots_dir))
}

fn process_test_file(entry: &globwalk::DirEntry) -> Result<FileInput> {
	let name = entry.path().file_stem().unwrap().to_str().expect("valid utf-8");

	// eprintln!("current: integration, {}", name);
	let snapshots_dir = PathBuf::from(format!("./snapshots/integrations/filename.out"));
	fs::create_dir_all(&snapshots_dir)?;

	Ok((String::from(name), PathBuf::from(entry.path()), snapshots_dir))
}

fn run() -> Result<()> {
	let args: Vec<String> = env::args().collect();
	let root_dir = &args[1];

	env::set_current_dir(root_dir)?;

	let areas = glob("area-data/*-*/*/*.yaml")?
		.into_iter()
		.map(|entry| process_area_file(&entry.unwrap()).unwrap());

	let integration_tests = glob("integrations/*.yaml")?
		.into_iter()
		.map(|entry| process_test_file(&entry.unwrap()).unwrap());

	let input_files: Vec<_> = areas.chain(integration_tests).collect();

	input_files.into_par_iter().for_each(|input| {
		eprintln!("{} [start]", &input.0);
		match convert_file(&input) {
			Ok(_) => {
				// eprintln!("{} [completed]", input.0)
			}
			Err(err) => eprintln!("{} [error]: {}", input.0, err),
		}
	});

	Ok(())
}

fn main() {
	if let Err(err) = run() {
		println!("error running example: {}", err);
		process::exit(1);
	}
}
