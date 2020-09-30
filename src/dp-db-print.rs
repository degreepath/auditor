use clap::Clap;

use formatter::area_of_study::AreaOfStudy;
use formatter::student::Student;
use formatter::to_csv::{CsvOptions, ToCsv};
use formatter::to_prose::{ProseContext, ProseOptions};
use rusqlite::{named_params, Connection, OpenFlags};

/// This doc string acts as a help message when the user runs '--help'
/// as do all doc strings on fields
#[derive(Clap)]
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
    /// Sets a custom config file.
    stnum: String,
    /// Output the data as text format
    #[clap(long)]
    as_text: bool,
    /// Output the data as HTML
    #[clap(long)]
    as_html: bool,
    /// Output the data as CSV
    #[clap(long)]
    as_csv: bool,
    /// pivot the csv
    #[clap(long)]
    pivot: bool,
    /// Output the data as JSON
    #[clap(long)]
    as_json: bool,
    /// Output the data as rust #[derive(Debug)]
    #[clap(long)]
    as_debug: bool,
}

fn main() {
    let opts: Opts = Opts::parse();

    let conn = Connection::open_with_flags(opts.db_path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();

    let branch = "cond-6";

    let mut stmt = conn.prepare("
        SELECT b.result, sd.input_data
        FROM branch b
            LEFT JOIN server_data sd on (b.stnum, b.catalog, b.code) = (sd.stnum, sd.catalog, sd.code)
        WHERE b.branch = :branch
            AND b.catalog = :catalog
            AND b.code = :code
            AND b.stnum = :stnum
        ORDER BY b.catalog, b.code, b.stnum
    ").unwrap();

    let params = named_params! {
        ":code": opts.area_code,
        ":branch": branch,
        ":catalog": opts.catalog,
        ":stnum": opts.stnum,
    };

    let results = stmt
        .query_map_named(params, |row| {
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
        })
        .unwrap()
        .map(|x| x.unwrap())
        .collect::<Vec<_>>();

    let (student, result) = results.first().expect("no matching student found");

    if opts.as_json {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    } else if opts.as_debug {
        println!("{:#?}", result);
    } else if opts.as_csv {
        let mut wtr = csv::WriterBuilder::new()
            .has_headers(false)
            .from_writer(std::io::stdout());

        let options = CsvOptions {};

        let records = result.get_record(&student, &options, false);

        let headers: Vec<_> = records.iter().map(|(a, _b)| a).collect();
        let row: Vec<_> = records.iter().map(|(_a, b)| b).collect();

        // eprintln!("{:#?}", headers);
        // eprintln!("{:#?}", row);

        if opts.pivot {
            wtr.write_record(&["column", "value"]).unwrap();

            for (header, cell) in headers.iter().zip(row.iter()) {
                wtr.write_record(&[header, cell]).unwrap();
            }
        } else {
            wtr.write_record(headers).unwrap();
            wtr.write_record(row).unwrap();
        }

        wtr.flush().unwrap();
    } else if opts.as_html {
        unimplemented!()
    } else if opts.as_text {
        println!(
            "{}",
            ProseContext {
                result: &result,
                options: &ProseOptions {
                    show_paths: true,
                    show_ranks: true,
                },
                student: &student,
            }
        );
    } else {
        unimplemented!()
    }
}
