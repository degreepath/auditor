use crate::structs::MappedResult;
use formatter::area_of_study::AreaOfStudy;
use formatter::student::{AreaOfStudy as AreaPointer, Emphasis, Student};
use formatter::to_csv::{CsvOptions, ToCsv};
use itertools::Itertools;
use serde_path_to_error;
use std::collections::{BTreeMap, BTreeSet, HashMap};

pub(crate) fn report_for_area_by_catalog(
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
                name,
                classification,
            }
        });

    let results: Vec<MappedResult> = {
        let mut r = results.collect::<Vec<_>>();

        r.sort_by_cached_key(|s| (s.emphases.join(","), s.name.clone(), s.stnum.clone()));

        r
    };

    Ok(results)
}

pub(crate) fn print_as_html<W: std::io::Write>(
    mut writer: &mut W,
    results: Vec<MappedResult>,
) -> anyhow::Result<()> {
    #[derive(Default)]
    struct Table {
        caption: String,
        header: Vec<String>,
        rows: Vec<Vec<String>>,
    }

    let grouped: HashMap<_, _> = results
        .into_iter()
        .map(|res| {
            (
                (
                    // res.catalog.clone(),
                    res.requirements.clone(),
                    res.emphasis_req_names.clone(),
                    res.header.clone(),
                ),
                res,
            )
        })
        .into_group_map();

    let grouped: BTreeMap<_, _> = grouped.iter().collect();

    let tables: Vec<Table> = grouped
        .into_iter()
        .map(|((_requirements, emphasis_req_names, header), group)| {
            let mut current_table: Table = Table::default();

            let catalogs = group
                .iter()
                .map(|res| res.catalog.clone())
                .collect::<BTreeSet<_>>();
            let catalog = catalogs.into_iter().collect::<Vec<_>>().join(", ");

            // write out a blank line, then a line with the new catalog year
            current_table.caption = if !emphasis_req_names.is_empty() {
                format!(
                    "Catalog: {}; Emphases: {}",
                    catalog,
                    emphasis_req_names.join(" & ")
                )
            } else {
                format!("Catalog: {}", catalog)
            };

            current_table.header = header.clone();

            current_table.rows = group
                .iter()
                .map(|result| {
                    let MappedResult { data, .. } = result;

                    let data = if data.len() != current_table.header.len() {
                        let mut d = data.clone();
                        d.resize(current_table.header.len(), String::from(""));
                        d
                    } else {
                        data.clone()
                    };

                    data
                })
                .collect();

            current_table
        })
        .collect();

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
            for td in tr {
                let attrs = if !td.contains("✗") && !td.trim().is_empty() {
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
