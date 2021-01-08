use crate::structs::MappedResult;
use itertools::Itertools;
use std::collections::{BTreeMap, BTreeSet, HashMap};

pub(crate) fn print_as_html<W: std::io::Write>(
    mut writer: &mut W,
    results: &[MappedResult],
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
