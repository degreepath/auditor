use crate::students::{StudentRecord, TableGroup, TableKey};
use formatter::{student::StudentClassification, to_record::Record};
use indexmap::IndexMap;
use itertools::Itertools;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Default, Debug)]
struct Table {
    caption: String,
    header: Vec<TableKey>,
    rows: Vec<IndexMap<TableKey, Vec<Record>>>,
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

struct TableKeysHolder {
    title: TableKey,
    overall: TableKey,
    sr: TableKey,
    jr: TableKey,
    so: TableKey,
    fy: TableKey,
}

pub(crate) fn print_as_html<'a, W: std::io::Write>(
    mut writer: &mut W,
    results: &[StudentRecord],
) -> anyhow::Result<()> {
    let keys = TableKeysHolder {
        title: TableKey {
            title: String::from("Requirement"),
            subtitle: None,
        },
        overall: TableKey {
            title: String::from("Needed Overall"),
            subtitle: None,
        },
        sr: TableKey {
            title: String::from("Needed by SR"),
            subtitle: None,
        },
        jr: TableKey {
            title: String::from("Needed by JR"),
            subtitle: None,
        },
        so: TableKey {
            title: String::from("Needed by SO"),
            subtitle: None,
        },
        fy: TableKey {
            title: String::from("Needed by FY"),
            subtitle: None,
        },
    };

    let catalog_groups = results
        .iter()
        .map(|result| result.group.by_titles())
        .unique()
        .into_group_map()
        .into_iter()
        .sorted_by_key(|(_k, v)| v.clone())
        .collect::<Vec<_>>();

    let tables = {
        let mut tables = vec![];

        for (keys, catalogs) in catalog_groups {
            for catalog in catalogs {
                let matching = results.iter().filter(|r| r.group.catalog == catalog);
            }
        }
    };

    let mut tables: Vec<Table> = results
        .iter()
        .map(|record| (record.group.titles_only(), record))
        .into_group_map()
        .iter()
        .map(|(group_header, group)| to_table(&group_header, &group, &keys))
        .collect();

    tables.sort_by_cached_key(|t| t.caption.clone());

    render_tables(&mut writer, &tables)?;

    Ok(())
}

fn to_table<'a>(headers: &TableGroup, group: &[&StudentRecord], keys: &TableKeysHolder) -> Table {
    let mut table: Table = Table::default();

    table.caption = format!("Catalog: {}", headers.catalog);

    table.header = vec![
        keys.title.clone(),
        keys.overall.clone(),
        keys.sr.clone(),
        keys.jr.clone(),
        keys.so.clone(),
        keys.fy.clone(),
    ];

    // count the number of passing items for each key
    let counters = {
        let mut counters: IndexMap<&TableKey, TableCounter> = headers
            .titles
            .iter()
            .filter(|title| title.title != "student")
            .map(|title| (title, TableCounter::default()))
            .collect();

        for key in headers.titles.iter() {
            let matches = group.iter().filter_map(|result| {
                result
                    .get_cell_by_key(key)
                    .and_then(|record| Some((result, record)))
            });
            for (result, record) in matches {
                let classification = &result.student.classification;
                let item = StudentOk {
                    name: result.student.name_sort.clone(),
                    stnum: result.student.stnum.clone(),
                    ok: record.is_ok(),
                };

                counters.entry(key).and_modify(|c| {
                    c.insert_into_classification(classification, item);
                });
            }
        }

        counters
    };

    // generate the rows from the counters
    let rows: Vec<IndexMap<TableKey, Vec<Record>>> = counters
        .into_iter()
        .map(|(key, value)| {
            let mut map = IndexMap::new();
            map.insert(
                keys.title.clone(),
                vec![Record::new(&keys.title.title, &key.title)],
            );
            map.insert(
                keys.overall.clone(),
                vec![Record::new(
                    &keys.overall.title,
                    &value.format_classification(&value.all),
                )],
            );
            map.insert(
                keys.sr.clone(),
                vec![Record::new(
                    &keys.sr.title,
                    &value.format_classification(&value.sr),
                )],
            );
            map.insert(
                keys.jr.clone(),
                vec![Record::new(
                    &keys.jr.title,
                    &value.format_classification(&value.jr),
                )],
            );
            map.insert(
                keys.so.clone(),
                vec![Record::new(
                    &keys.so.title,
                    &value.format_classification(&value.so),
                )],
            );
            map.insert(
                keys.fy.clone(),
                vec![Record::new(
                    &keys.fy.title,
                    &value.format_classification(&value.fy),
                )],
            );
            map
        })
        .collect();

    table.rows = rows;

    table
}

fn render_tables<W: std::io::Write>(mut writer: &mut W, tables: &[Table]) -> anyhow::Result<()> {
    writeln!(&mut writer, r#"<meta charset="utf-8">"#)?;

    for table in tables {
        if !table.caption.is_empty() {
            writeln!(&mut writer, "<h2>{}</h2>", table.caption)?;
        }
        writeln!(&mut writer, "<table>")?;
        writeln!(&mut writer, "<thead>")?;
        writeln!(&mut writer, "<tr>")?;
        for th in table.header.iter() {
            writeln!(&mut writer, "<th>{}</th>", th.title)?;
        }
        writeln!(&mut writer, "</tr>")?;
        if table.header.iter().any(|th| th.subtitle.is_some()) {
            writeln!(&mut writer, "<tr>")?;
            for th in table.header.iter() {
                if let Some(text) = &th.subtitle {
                    writeln!(&mut writer, "<th>{}</th>", text)?;
                } else {
                    writeln!(&mut writer, "<th></th>")?;
                }
            }
            writeln!(&mut writer, "</tr>")?;
        }
        writeln!(&mut writer, "</thead>")?;

        writeln!(&mut writer, "<tbody>")?;
        for tr in table.rows.iter() {
            writeln!(&mut writer, "<tr>")?;
            for (i, cells) in tr.values().enumerate() {
                for cell in cells.iter() {
                    let attrs = if i == 0 {
                        r#"class="""#
                    // } else if td.starts_with("0") {
                    //     "class=\"passing\""
                    } else {
                        r#"class="not-passing""#
                    };

                    writeln!(&mut writer, "<td {}>", attrs)?;

                    let content = cell.content.iter().map(|c| c.render());
                    let interspersed =
                        itertools::Itertools::intersperse(content, String::from("<br>"));
                    for text in interspersed {
                        if text == "<br>" {
                            writeln!(&mut writer, "<br>")?;
                        } else {
                            writeln!(
                                &mut writer,
                                "{}",
                                askama_escape::escape(&text, askama_escape::Html)
                            )?;
                        }
                    }
                    writeln!(&mut writer, "</td>")?;
                }
            }
            writeln!(&mut writer, "</tr>")?;
        }
        // for tr in table.rows {
        //     writeln!(&mut writer, "<tr>")?;
        //     for (i, td) in tr.iter().enumerate() {
        //         let attrs = if i == 0 {
        //             "class=\"\""
        //         } else if td.starts_with("0") {
        //             "class=\"passing\""
        //         } else {
        //             "class=\"not-passing\""
        //         };
        //         writeln!(
        //             &mut writer,
        //             "<td {}>{}</td>",
        //             attrs,
        //             askama_escape::escape(&td, askama_escape::Html)
        //         )?;
        //     }
        //     writeln!(&mut writer, "</tr>")?;
        // }
        writeln!(&mut writer, "</tbody>")?;
        writeln!(&mut writer, "</table>")?;
    }

    Ok(())
}
