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
    catalog: String,
    /// Sets a custom config file.
    area_code: String,
}

fn main() {
    let opts: Opts = Opts::parse();

    report_for_area_by_catalog(opts.db_path, &opts.catalog, &opts.area_code).unwrap();
}

pub fn report_for_area_by_catalog<P: AsRef<Path>>(
    db_path: P,
    catalog: &str,
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
            AND b.catalog = :catalog
            AND b.code = :code
        ORDER BY b.stnum, b.catalog, b.code
    ").unwrap();

    let params = named_params! {
        ":catalog": catalog,
        ":code": area_code,
        ":branch": branch,
    };

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

    for (i, pair) in results.enumerate() {
        let (student, result) = pair.unwrap();

        let records = result.get_record(&student, &options, false);

        if i == 0 {
            let headers: Vec<_> = records.iter().map(|(a, _b)| a).collect();
            wtr.write_record(headers).unwrap();
        }

        let row: Vec<_> = records.iter().map(|(_a, b)| b).collect();
        // dbg!(&records);
        wtr.write_record(row).unwrap();
        wtr.flush().unwrap();
    }

    // wtr.flush().unwrap();

    Ok(())
}
