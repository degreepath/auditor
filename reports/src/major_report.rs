use crate::students::{StudentRecord, TableGroup, TableKey};
use formatter::to_record::Record;
use itertools::Itertools;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Default, Debug)]
struct Table {
    caption: String,
    header: Vec<TableKey>,
    rows: Vec<BTreeMap<TableKey, Vec<Record>>>,
}

pub(crate) fn print_as_html<'a, W: std::io::Write>(
    mut writer: &mut W,
    results: &[StudentRecord],
) -> anyhow::Result<()> {
    let grouped = results
        .iter()
        .map(|record| ((record.group.clone(), record.emphasis_requirement_names.clone()), record))
        .into_group_map();

    let mut tables: Vec<Table> = grouped
        .iter()
        .map(|((group_header, emphasis_names), group)| {
            to_table(&group_header, &emphasis_names, &group)
        })
        .collect();

    tables.sort_by_cached_key(|t| t.caption.clone());

    render_tables(&mut writer, &tables)?;

    Ok(())
}

fn to_table<'a>(
    headers: &TableGroup,
    emphasis_names: &[String],
    group: &[&'a StudentRecord],
) -> Table {
    let mut current_table = Table::default();

    let catalogs = group
        .iter()
        .map(|res| res.student.catalog.clone())
        .collect::<BTreeSet<_>>()
        .iter()
        .join(", ");

    // write out a blank line, then a line with the new catalog year
    current_table.caption = if !emphasis_names.is_empty() {
        format!(
            "Catalog: {}; Emphases: {}",
            catalogs,
            emphasis_names.join(" & ")
        )
    } else {
        format!("Catalog: {}", catalogs)
    };

    current_table.header = headers.titles.clone();

    current_table.rows = {
        let mut rows = vec![];

        for result in group {
            let mut row: BTreeMap<TableKey, Vec<Record>> = BTreeMap::new();

            for column in headers.titles.clone() {
                if let Some(record) = result.get_cell_by_key(&column) {
                    let entry = row.entry(column).or_default();
                    entry.push(record.clone());
                } else {
                    println!("did not find cell for {:?}", &column);
                    println!("known cells:");
                    for cell in result.get_all_cells() {
                        println!("- {} ({})", cell.0, cell.1);
                    }
                }
            }

            rows.push(row);
        }

        rows
    };

    current_table
}

fn render_tables<W: std::io::Write>(mut writer: &mut W, tables: &[Table]) -> anyhow::Result<()> {
    writeln!(&mut writer, r#"<meta charset="utf-8">"#)?;

    for table in tables {
        if !table.caption.is_empty() {
            writeln!(&mut writer, "<h2>{}</h2>", table.caption)?;
        }
        writeln!(&mut writer, r#"<table class="dp-report">"#)?;
        writeln!(&mut writer, "<thead>")?;
        writeln!(&mut writer, "<tr>")?;
        for th in table.header.iter() {
            writeln!(&mut writer, "<th>{}</th>", th.title)?;
        }
        writeln!(&mut writer, "</tr>")?;
        writeln!(&mut writer, "<tr>")?;
        for th in table.header.iter() {
            if let Some(text) = &th.subtitle {
                writeln!(&mut writer, "<th>{}</th>", text)?;
            } else {
                writeln!(&mut writer, "<th></th>")?;
            }
        }
        writeln!(&mut writer, "</tr>")?;
        writeln!(&mut writer, "</thead>")?;

        writeln!(&mut writer, "<tbody>")?;
        for tr in table.rows.iter() {
            writeln!(&mut writer, "<tr>")?;
            for th in table.header.iter() {
                let cells = tr.get(th).unwrap();

                for cell in cells {
                    let class_list = vec![
                        if cell.is_ok() {
                            "passing"
                        } else {
                            "not-passing"
                        },
                        cell.status_class(),
                    ]
                    .iter()
                    .join(" ");

                    let content = cell.content.iter().map(|c| c.render()).join("<br>");

                    writeln!(
                        &mut writer,
                        r#"<td class="{}">{}</td>"#,
                        class_list,
                        &content,
                        // askama_escape::escape(&td, askama_escape::Html)
                    )?;
                }
            }
            writeln!(&mut writer, "</tr>")?;
        }
        writeln!(&mut writer, "</tbody>")?;
        writeln!(&mut writer, "</table>")?;
    }

    Ok(())
}
