use crate::structs::MappedResult;
use formatter::student::StudentClassification;
use itertools::Itertools;
use std::collections::{BTreeMap, BTreeSet};

pub(crate) fn print_as_html<W: std::io::Write>(
    mut writer: &mut W,
    results: &[MappedResult],
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
