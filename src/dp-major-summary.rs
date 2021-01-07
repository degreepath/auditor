use clap::Clap;
use formatter::area_of_study::AreaOfStudy;
use formatter::database;
use formatter::student::{AreaOfStudy as AreaPointer, Emphasis};
use formatter::student::{Student, StudentClassification};
use formatter::to_csv::{CsvOptions, ToCsv};
use itertools::Itertools;
use serde_path_to_error;
use std::collections::{BTreeMap, BTreeSet};

// TODO: build one dp-report binary that executes a subcommand for report, summary, and required

/// This doc string acts as a help message when the user runs '--help'
/// as do all doc strings on fields
#[derive(Clap, Debug)]
#[clap(
    version = "1.0",
    author = "Hawken MacKay Rives <degreepath@hawkrives.fastmail.fm>"
)]
struct Opts {
    /// Which area of study to look up
    area_code: String,
    /// Enables header debugging
    #[clap(long)]
    debug: bool,
    /// Outputs the data as HTML tables
    #[clap(long)]
    as_html: bool,
    /// Outputs the data as a single CSV document
    #[clap(long)]
    as_csv: bool,
    /// Stores the data into Postgres
    #[clap(long)]
    to_database: bool,
}

fn main() -> anyhow::Result<()> {
    let opts: Opts = Opts::parse();

    let mut client = database::connect()?;
    let results = report_for_area_by_catalog(&mut client, &opts.area_code).unwrap();

    if opts.as_csv {
        print_as_csv(&opts, results);
    } else if opts.as_html {
        use std::io::Cursor;

        let mut buff = Cursor::new(Vec::new());
        print_as_html(&opts, &mut buff, results)?;

        let inner_buff = buff.into_inner();
        let as_html = std::str::from_utf8(&inner_buff)?;
        if opts.to_database {
            database::record_report(
                &mut client,
                database::ReportType::Summary,
                &opts.area_code,
                as_html,
            )?;
        } else {
            print!("{}", as_html);
        };
    } else {
        unimplemented!("either --as-csv or --as-html must be given");
    };

    Ok(())
}

struct MappedResult {
    header: Vec<String>,
    data: Vec<String>,
    catalog: String,
    stnum: String,
    requirements: Vec<String>,
    emphases: Vec<String>,
    emphasis_req_names: Vec<String>,
    name: String,
    classification: StudentClassification,
}

fn report_for_area_by_catalog(
    client: &mut postgres::Client,
    area_code: &str,
) -> anyhow::Result<Vec<MappedResult>> {
    let mut tx = client.transaction()?;

    let stmt = tx.prepare(
        "
        SELECT cast(result as text) as result
             , cast(input_data as text) as input_data
        FROM result
        WHERE area_code = $1 AND is_active = true AND result_version = 3
        ORDER BY area_code, student_id
    ",
    )?;

    let options = CsvOptions {};

    let results = tx
        .query(&stmt, &[&area_code])?
        .into_iter()
        .map(|row| {
            let result: String = row.get(0);
            let student: String = row.get(1);

            let student_deserializer = &mut serde_json::Deserializer::from_str(student.as_str());
            let student: Student = match serde_path_to_error::deserialize(student_deserializer) {
                Ok(r) => r,
                Err(err) => {
                    eprintln!("student error");

                    eprintln!("{}", student);
                    dbg!(err);

                    panic!();
                }
            };

            // let value: serde_json::Value = serde_json::from_str(&result).unwrap();
            // let result = serde_json::to_string_pretty(&value).unwrap();

            let result_deserializer = &mut serde_json::Deserializer::from_str(result.as_str());
            let result: AreaOfStudy = match serde_path_to_error::deserialize(result_deserializer) {
                Ok(r) => r,
                Err(err) => {
                    eprintln!("result error");

                    eprintln!("{}", result);
                    eprintln!("{}", err);
                    eprintln!("at {}", err.path());
                    dbg!(student.stnum);

                    panic!();
                }
            };

            (student, result)
        })
        .map(|(student, result)| {
            // TODO: handle case where student's catalog != area's catalog
            let catalog = student.catalog.clone();
            let stnum = student.stnum.clone();
            let name = student.name.clone();
            let classification = student.classification.clone();

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

            let mut header: Vec<String> = Vec::with_capacity(records.len());
            let mut data: Vec<String> = Vec::with_capacity(records.len());

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
                classification,
                name,
            }
        });

    let results: Vec<MappedResult> = {
        let mut r = results.collect::<Vec<_>>();

        r.sort_by_cached_key(|s| {
            return (s.catalog.clone(), s.emphases.join(","), s.stnum.clone());
        });

        r
    };

    Ok(results)
}

fn print_as_csv(opts: &Opts, results: Vec<MappedResult>) -> () {
    let mut wtr = csv::WriterBuilder::new()
        .has_headers(false)
        .from_writer(std::io::stdout());

    let longest_header = results
        .iter()
        .map(|r: &MappedResult| std::cmp::max(r.header.len(), r.data.len()))
        .max()
        .unwrap();

    let mut last_header: Vec<String> = Vec::new();
    let mut last_requirements: Vec<String> = Vec::new();
    let mut last_catalog: String = String::from("");

    for (i, pair) in results.into_iter().enumerate() {
        let MappedResult {
            mut header,
            mut data,
            requirements,
            catalog,
            emphasis_req_names,
            emphases: _,
            stnum: _,
            classification: _,
            name: _,
        } = pair;

        // make sure that we have enough columns
        header.resize(longest_header, String::from(""));

        if opts.debug && last_header != header {
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
        } else if last_requirements != requirements || last_catalog != catalog {
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

        data.resize(longest_header, String::from(""));

        wtr.write_record(data).unwrap();
    }

    wtr.flush().unwrap();
}

fn print_as_html<W: std::io::Write>(
    _opts: &Opts,
    mut writer: &mut W,
    results: Vec<MappedResult>,
) -> anyhow::Result<()> {
    #[derive(Default, Debug)]
    struct Table {
        caption: String,
        header: Vec<String>,
        rows: Vec<Vec<String>>,
    }

    #[derive(Default, Clone, Debug)]
    struct StudentOk {
        stnum: String,
        name: String,
        ok: bool,
    }

    #[derive(Default, Clone, Debug)]
    struct TableCounter {
        all: Vec<StudentOk>,
        sr: Vec<StudentOk>,
        jr: Vec<StudentOk>,
        so: Vec<StudentOk>,
        fy: Vec<StudentOk>,
        nc: Vec<StudentOk>,
    }

    impl TableCounter {
        fn insert_into_classification(
            &mut self,
            classification: &StudentClassification,
            item: StudentOk,
        ) -> () {
            self.all.push(item.clone());
            match classification {
                StudentClassification::SR => self.sr.push(item),
                StudentClassification::JR => self.jr.push(item),
                StudentClassification::SO => self.so.push(item),
                StudentClassification::FY => self.fy.push(item),
                StudentClassification::NC => self.nc.push(item),
            };
        }

        fn format_classification(&self, items: &[StudentOk]) -> String {
            let all_ok = items.iter().filter(|ok| ok.ok).collect::<Vec<_>>().len();
            let all_all = items.len();

            format!("{} of {}", all_all - all_ok, all_all)
        }
    }

    fn skip_non_required_columns(text: &str) -> bool {
        !(text == "student")
    }

    let grouped = results
        .into_iter()
        .map(|res| {
            // let catalog = res.catalog.clone();
            // let requirements = res.requirements.clone();
            // let emph = res.emphasis_req_names.clone();

            let headers = res
                .header
                .iter()
                .filter(|s| skip_non_required_columns(&s))
                .cloned()
                .collect::<Vec<_>>();

            (headers, res)
        })
        .into_group_map();

    let mut tables: Vec<Table> = grouped
        .into_iter()
        .map(|(group_header, group)| {
            let mut current_table: Table = Table::default();

            // write out a blank line, then a line with the new catalog year
            let catalogs = group
                .iter()
                .map(|res| res.catalog.clone())
                .collect::<BTreeSet<_>>();
            let catalog = catalogs.into_iter().collect::<Vec<_>>().join(", ");

            current_table.caption = format!("Catalog: {}", catalog);
            // current_table.caption = if !emphasis_req_names.is_empty() {
            //     format!(
            //         "Catalog: {}; Emphases: {}",
            //         catalog,
            //         emphasis_req_names.join(" & ")
            //     )
            // } else {
            //     format!("Catalog: {}", catalog)
            // };

            let top_headers = vec![
                "".into(),
                "Needed Overall".into(),
                "Needed by SR".into(),
                "Needed by JR".into(),
                "Needed by SO".into(),
                "Needed by FY".into(),
                // "Needed by NC".into(),
            ];

            current_table.header = top_headers.clone();

            let mut counters: BTreeMap<(usize, &String), TableCounter> = BTreeMap::new();
            for (i, cell) in group_header.iter().enumerate() {
                counters.insert((i, cell), TableCounter::default());
            }

            for result in group.iter() {
                let MappedResult {
                    header: local_header,
                    data: local_data,
                    requirements: _,
                    catalog: _,
                    emphasis_req_names: _,
                    stnum,
                    classification,
                    emphases: _,
                    name,
                } = result;

                let cells = local_header
                    .iter()
                    .zip_eq(local_data)
                    .filter(|(header, _)| skip_non_required_columns(header));

                for (i, (header, cell)) in cells.enumerate() {
                    counters.entry((i, header)).and_modify(|c| {
                        let is_ok = !cell.contains("✗") && !cell.trim().is_empty();
                        let item = StudentOk {
                            name: name.clone(),
                            stnum: stnum.clone(),
                            ok: is_ok,
                        };
                        c.insert_into_classification(classification, item)
                    });
                }
            }

            let rows: Vec<Vec<String>> = counters
                .iter()
                .map(|((_i, key), value)| {
                    vec![
                        (*key).clone(),
                        value.format_classification(&value.all),
                        value.format_classification(&value.sr),
                        value.format_classification(&value.jr),
                        value.format_classification(&value.so),
                        value.format_classification(&value.fy),
                        // value.format_classification(&value.nc),
                    ]
                })
                .collect();

            current_table.rows = rows;

            current_table
        })
        .collect();

    tables.sort_by_cached_key(|t| t.caption.clone());

    writeln!(&mut writer, r#"<meta charset="utf-8">"#)?;

    for table in tables {
        if !table.caption.is_empty() {
            writeln!(&mut writer, "<h2>{}</h2>", table.caption)?;
        }
        writeln!(&mut writer, "<table>")?;
        writeln!(&mut writer, "<thead>")?;
        writeln!(&mut writer, "<tr>")?;
        for th in table.header {
            writeln!(&mut writer, "<th>{}</th>", th)?;
        }
        writeln!(&mut writer, "</tr>")?;
        writeln!(&mut writer, "</thead>")?;

        writeln!(&mut writer, "<tbody>")?;
        for tr in table.rows {
            writeln!(&mut writer, "<tr>")?;
            for (i, td) in tr.iter().enumerate() {
                let attrs = if i == 0 {
                    "class=\"\""
                } else if td.starts_with("0") {
                    "class=\"passing\""
                } else {
                    "class=\"not-passing\""
                };
                writeln!(
                    &mut writer,
                    "<td {}>{}</td>",
                    attrs,
                    askama_escape::escape(&td, askama_escape::Html)
                )?;
            }
            writeln!(&mut writer, "</tr>")?;
        }
        writeln!(&mut writer, "</tbody>")?;
        writeln!(&mut writer, "</table>")?;
    }

    Ok(())
}
