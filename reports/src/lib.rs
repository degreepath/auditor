pub mod database;
mod major_report;
mod major_summary;
mod structs;

pub enum ReportType {
    Report,
    Summary,
}

pub fn run_report(
    mut client: &mut postgres::Client,
    report_type: &ReportType,
    area_code: &str,
) -> anyhow::Result<String> {
    let report_for_area_by_catalog = match report_type {
        ReportType::Report => major_report::report_for_area_by_catalog,
        ReportType::Summary => major_summary::report_for_area_by_catalog,
    };

    let print_as_html = match report_type {
        ReportType::Report => major_report::print_as_html,
        ReportType::Summary => major_summary::print_as_html,
    };

    let results = report_for_area_by_catalog(&mut client, &area_code)?;

    let mut buff = std::io::Cursor::new(Vec::new());
    print_as_html(&mut buff, results)?;

    let inner_buff = buff.into_inner();
    Ok(String::from(std::str::from_utf8(&inner_buff)?))
}

// pub fn save_report()
