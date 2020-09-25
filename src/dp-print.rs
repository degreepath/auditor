use clap::Clap;

use formatter::area_of_study::AreaOfStudy;
use formatter::student::Student;
use formatter::to_csv::{CsvOptions, ToCsv};
use formatter::to_prose::{ProseContext, ProseOptions};

/// This doc string acts as a help message when the user runs '--help'
/// as do all doc strings on fields
#[derive(Clap)]
#[clap(
    version = "1.0",
    author = "Hawken MacKay Rives <degreepath@hawkrives.fastmail.fm>"
)]
struct Opts {
    /// Sets a custom config file.
    student_file: String,
    /// Sets a custom config file.
    input_file: String,
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

    let student: Student = {
        let contents = std::fs::read_to_string(opts.student_file)
            .expect("Something went wrong reading the file");

        serde_json::from_str(&contents).unwrap()
    };

    let result: AreaOfStudy = {
        let contents = std::fs::read_to_string(opts.input_file)
            .expect("Something went wrong reading the file");

        serde_json::from_str(&contents).unwrap()
    };

    if opts.as_json {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    } else if opts.as_debug {
        println!("{:#?}", result);
    } else if opts.as_csv {
        let mut wtr = csv::WriterBuilder::new()
            .has_headers(false)
            .from_writer(std::io::stdout());

        let options = CsvOptions {};

        let records = result.get_record(&student, &options);

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
