use clap::Clap;
use reports::database::{collect_area_codes, connect, record_report};
use reports::students::fetch_records;
use reports::{run_report, ReportType};

const AUTHOR: &'static str = "Hawken MacKay Rives <degreepath@hawkrives.fastmail.fm>";
/// This doc string acts as a help message when the user runs '--help'
/// as do all doc strings on fields
#[derive(Clap)]
#[clap(version = "1.0", author = AUTHOR)]
struct Opts {
    #[clap(subcommand)]
    action: SubCommand,
}

#[derive(Clap)]
enum SubCommand {
    Report(SubCmd),
    Summarize(SubCmd),
    Batch(BatchSubCmd),
}

/// A subcommand for controlling testing
#[derive(Clap)]
struct SubCmd {
    /// Which area of study to look up
    area_code: String,
    /// Stores the data into Postgres
    #[clap(long)]
    to_database: bool,
}

/// A subcommand for controlling testing
#[derive(Clap)]
struct BatchSubCmd {
    /// Stores the data into Postgres
    #[clap(long)]
    to_database: bool,
}

fn main() -> anyhow::Result<()> {
    let opts: Opts = Opts::parse();

    let mut client = connect()?;

    match opts.action {
        SubCommand::Report(sopts) => {
            let report_type = ReportType::Report;
            let records = fetch_records(&mut client, &sopts.area_code)?;
            let report = run_report(&records, &report_type)?;

            if sopts.to_database {
                record_report(&mut client, &report_type, &sopts.area_code, &report)?;
            } else {
                print!("{}", report);
            };
        }
        SubCommand::Summarize(sopts) => {
            let report_type = ReportType::Summary;
            let records = fetch_records(&mut client, &sopts.area_code)?;
            let report = run_report(&records, &report_type)?;

            if sopts.to_database {
                record_report(&mut client, &report_type, &sopts.area_code, &report)?;
            } else {
                print!("{}", report);
            };
        }
        SubCommand::Batch(sopts) => {
            use std::io::Write;
            use std::time::Instant;

            let area_codes = collect_area_codes(&mut client)?;

            for area_code in area_codes {
                print!("{} | ", area_code);
                std::io::stdout().flush()?;
                let start = Instant::now();
                let records = fetch_records(&mut client, &area_code)?;
                print!("loaded {} in {:?}; ", records.len(), start.elapsed());

                for report_type in &[ReportType::Report, ReportType::Summary] {
                    let start = Instant::now();

                    match report_type {
                        ReportType::Report => print!("report: "),
                        ReportType::Summary => print!("summary: "),
                    };
                    let report = run_report(&records, &report_type)?;
                    if sopts.to_database {
                        record_report(&mut client, &report_type, &area_code, &report)?;
                    }

                    print!("done in {:?}; ", start.elapsed());
                    std::io::stdout().flush()?;
                }
                println!();
            }
        }
    };

    Ok(())
}
