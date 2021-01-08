pub mod database;
mod major_report;
mod major_summary;
mod structs;
pub mod students;

use structs::MappedResult;

pub enum ReportType {
    Report,
    Summary,
}

pub fn run_report(records: &[MappedResult], report_type: &ReportType) -> anyhow::Result<String> {
    let print_as_html = match report_type {
        ReportType::Report => major_report::print_as_html,
        ReportType::Summary => major_summary::print_as_html,
    };

    let mut buff = std::io::Cursor::new(Vec::new());
    print_as_html(&mut buff, records)?;

    let inner_buff = buff.into_inner();
    Ok(String::from(std::str::from_utf8(&inner_buff)?))
}

// pub fn save_report()
