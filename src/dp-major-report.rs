use clap::Clap;
use formatter::area_of_study::AreaOfStudy;
use formatter::student::Student;
use formatter::to_csv::{CsvOptions, ToCsv};
use rusqlite::{named_params, Connection, Error as RusqliteError, OpenFlags, Result};
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

    let results = stmt.query_map_named(params, |row| {
        let result: String = row.get(0).unwrap();
        let student: String = row.get(1).unwrap();

        let result: AreaOfStudy = match serde_json::from_str(&result) {
            Err(err) => {
                eprintln!("result error");
                let value: serde_json::Value = serde_json::from_str(&result).unwrap();
                dbg!(value);
                dbg!(err);

                panic!();
            }
            Ok(r) => r,
        };
        let student: Student = match serde_json::from_str(&student) {
            Err(err) => {
                eprintln!("student error");

                let value: serde_json::Value = serde_json::from_str(&student).unwrap();
                dbg!(value);
                dbg!(err);
                panic!();
            }
            Ok(r) => r,
        };

        Ok((student, result))
    })?;

    struct MappedResult {
        header: Vec<String>,
        data: Vec<String>,
        catalog: String,
    }

    let results = results.map(|pair| {
        let (student, result) = pair.unwrap();

        // TODO: handle case where student's catalog != area's catalog
        let catalog = student.catalog.clone();

        let records = result.get_record(&student, &options, false);

        let mut header: Vec<String> = Vec::new();
        let mut data: Vec<String> = Vec::new();

        for (th, td) in records.into_iter() {
            header.push(th);
            data.push(td);
        }

        MappedResult {
            header,
            data,
            catalog,
        }
    });

    let results = results.collect::<Vec<_>>();

    let longest_header = results.iter().map(|r| r.header.len()).max().unwrap();

    let mut last_catalog = String::from("");

    for pair in results.into_iter() {
        let MappedResult {
            mut header,
            mut data,
            catalog,
        } = pair;

        if last_catalog != catalog {
            // make sure that we have enough columns
            header.resize(longest_header, String::from(""));

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

            wtr.write_record(header).unwrap();
            last_catalog = catalog.clone();
        }

        data.resize(longest_header, String::from(""));

        wtr.write_record(data).unwrap();
    }

    wtr.flush().unwrap();

    Ok(())
}
