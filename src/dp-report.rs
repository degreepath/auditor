use clap::Clap;
use reports::database::{collect_area_codes, connect, record_report};
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
            let report = run_report(&mut client, &report_type, &sopts.area_code)?;

            if sopts.to_database {
                record_report(&mut client, &report_type, &sopts.area_code, &report)?;
            } else {
                print!("{}", report);
            };
        }
        SubCommand::Summarize(sopts) => {
            let report_type = ReportType::Summary;
            let report = run_report(&mut client, &report_type, &sopts.area_code)?;

            if sopts.to_database {
                record_report(&mut client, &report_type, &sopts.area_code, &report)?;
            } else {
                print!("{}", report);
            };
        }
        SubCommand::Batch(sopts) => {
            use std::time::{Instant};
            use std::io::Write;

            let area_codes = collect_area_codes(&mut client)?;

            for area_code in area_codes {
                print!("{} | ", area_code);
                std::io::stdout().flush()?;
                for report_type in &[ReportType::Report, ReportType::Summary] {
                    let start = Instant::now();

                    match report_type {
                        ReportType::Report => print!("report: "),
                        ReportType::Summary => print!("summary: "),
                    };
                    let report = run_report(&mut client, &report_type, &area_code)?;
                    if sopts.to_database {
                        record_report(&mut client, &report_type, &area_code, &report)?;
                    }

                    print!("done in {:?}; ", start.elapsed().as_millis());
                    std::io::stdout().flush()?;
                }
                println!();
            }
        }
    };

    Ok(())
}
