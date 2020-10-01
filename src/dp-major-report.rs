use clap::Clap;
use formatter::area_of_study::AreaOfStudy;
use formatter::student::Student;
use formatter::student::{AreaOfStudy as AreaPointer, Emphasis};
use formatter::to_csv::{CsvOptions, ToCsv};
use rusqlite::{named_params, Connection, Error as RusqliteError, OpenFlags, Result};
use std::collections::BTreeSet;
use std::path::Path;

/// This doc string acts as a help message when the user runs '--help'
/// as do all doc strings on fields
#[derive(Clap, Debug)]
#[clap(
    version = "1.0",
    author = "Hawken MacKay Rives <degreepath@hawkrives.fastmail.fm>"
)]
struct Opts {
    /// Sets the database path
    db_path: String,
    /// Sets a custom config file.
    area_code: String,
}

fn main() {
    let opts: Opts = Opts::parse();

    report_for_area_by_catalog(opts.db_path, &opts.area_code).unwrap();
}

pub fn report_for_area_by_catalog<P: AsRef<Path>>(
    db_path: P,
    area_code: &str,
    // ) -> Result<Vec<(Student, AreaOfStudy)>, RusqliteError> {
) -> Result<(), RusqliteError> {
    let conn = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;

    let branch = "cond-6";

    let mut stmt = conn.prepare("
        SELECT b.result, sd.input_data
        FROM branch b
            LEFT JOIN server_data sd on (b.stnum, b.catalog, b.code) = (sd.stnum, sd.catalog, sd.code)
        WHERE b.branch = :branch
            AND b.code = :code
        ORDER BY b.catalog, b.code, b.stnum
    ").unwrap();

    let params = named_params! {":code": area_code, ":branch": branch};

    let mut wtr = csv::WriterBuilder::new()
        .has_headers(false)
        .from_writer(std::io::stdout());

    let options = CsvOptions {};

    struct MappedResult {
        header: Vec<String>,
        data: Vec<String>,
        catalog: String,
        stnum: String,
        requirements: Vec<String>,
        emphases: Vec<String>,
        emphasis_req_names: Vec<String>,
    }

    let results = stmt
        .query_map_named(params, |row| {
            let result: String = row.get(0).unwrap();
            let student: String = row.get(1).unwrap();

            Ok((student, result))
        })?
        .map(|pair| pair.unwrap())
        .enumerate()
        .map(|(i, (student, result))| {
            eprintln!("{} of 3821", i);

            let value: serde_json::Value = serde_json::from_str(&student).unwrap();
            let student = serde_json::to_string_pretty(&value).unwrap();

            let student: Student = match serde_json::from_str(&student) {
                Ok(r) => r,
                Err(err) => {
                    eprintln!("student error");

                    eprintln!("{}", student);
                    dbg!(err);

                    panic!();
                }
            };

            let value: serde_json::Value = serde_json::from_str(&result).unwrap();
            let result = serde_json::to_string_pretty(&value).unwrap();

            let result: AreaOfStudy = match serde_json::from_str(&result) {
                Ok(r) => r,
                Err(err) => {
                    eprintln!("result error");

                    eprintln!("{}", result);
                    dbg!(err);
                    dbg!(student.stnum);

                    panic!();
                }
            };

            // TODO: handle case where student's catalog != area's catalog
            let catalog = student.catalog.clone();
            let stnum = student.stnum.clone();

            let records = result.get_record(&student, &options, false);
            let requirements = result.get_requirements();

            let emphases = student
                .areas
                .iter()
                .filter_map(|a| match a {
                    AreaPointer::Emphasis(Emphasis { name, .. }) => Some(name),
                    _ => None,
                })
                .cloned()
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();

            let emphasis_req_names = requirements
                .iter()
                .filter(|e| e.starts_with("Emphasis: "))
                .map(|name| String::from(name.split(" → ").take(1).last().unwrap()))
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();

            let mut header: Vec<String> = Vec::new();
            let mut data: Vec<String> = Vec::new();

            for (th, td) in records.into_iter() {
                header.push(th);
                data.push(td);
            }

            MappedResult {
                header,
                data,
                requirements,
                emphases,
                emphasis_req_names,
                catalog,
                stnum,
            }
        });

    let results: Vec<MappedResult> = {
        let mut r = results.collect::<Vec<_>>();

        r.sort_by_cached_key(|s| {
            return (s.catalog.clone(), s.emphases.join(","), s.stnum.clone());
        });

        r
    };

    let longest_header = results
        .iter()
        .map(|r: &MappedResult| std::cmp::max(r.header.len(), r.data.len()))
        .max()
        .unwrap();

    // let mut last_header: Vec<String> = Vec::new();
    let mut last_requirements: Vec<String> = Vec::new();
    let mut last_catalog = String::from("");

    for (i, pair) in results.into_iter().enumerate() {
        let MappedResult {
            mut header,
            mut data,
            requirements,
            emphases: _,
            catalog,
            emphasis_req_names,
            stnum: _,
        } = pair;

        // make sure that we have enough columns
        header.resize(longest_header, String::from(""));

        if last_requirements != requirements || catalog != last_catalog {
            if i != 0 {
                // write out a blank line, then a line with the new catalog year
                let blank = vec![""; longest_header];
                wtr.write_record(blank).unwrap();
            }

            // write out a blank line, then a line with the new catalog year
            let title = {
                let mut v = Vec::new();
                v.push(format!("Catalog: {}", catalog));
                v.push(emphasis_req_names.join(" & "));
                v.resize(longest_header, String::from(""));
                v
            };
            wtr.write_record(title).unwrap();

            last_requirements = requirements.clone();
            last_catalog = catalog.clone();
            wtr.write_record(header).unwrap();
        }

        /* if last_header != header {
            // write out a blank line, then a line with the new catalog year
            let blank = vec![""; longest_header];
            wtr.write_record(blank).unwrap();

            // write out a blank line, then a line with the new catalog year
            let title = {
                let mut v = Vec::new();
                v.push(format!("Catalog: {}", catalog));
                v.resize(longest_header, String::from(""));
                v
            };
            wtr.write_record(title).unwrap();

            last_header = header.clone();
            wtr.write_record(header).unwrap();
        } */

        data.resize(longest_header, String::from(""));

        wtr.write_record(data).unwrap();
    }

    wtr.flush().unwrap();

    Ok(())
}
