use formatter::student::Student;
use formatter::to_record::{RecordOptions, ToRecord};
use formatter::{area_of_study::AreaOfStudy, to_record::Record};
use itertools::Itertools;
use serde_path_to_error;

pub(crate) fn fetch_students(
    tx: &mut postgres::Transaction,
    area_code: &str,
) -> anyhow::Result<Vec<(Student, AreaOfStudy)>> {
    let stmt = "
        SELECT cast(result as text) as result
             , cast(input_data as text) as input_data
        FROM result
        WHERE area_code = $1 AND is_active = true AND result_version = 3
        ORDER BY area_code, student_id
    ";

    let iter = tx
        .query(stmt, &[&area_code])?
        .into_iter()
        .map(|row| {
            let result: String = row.get(0);
            let student: String = row.get(1);
            (result, student)
        })
        .map(|(result, student)| parse_record(&result, &student));

    Ok(iter.collect())
}

fn parse_record(result: &str, student: &str) -> (Student, AreaOfStudy) {
    let student_deserializer = &mut serde_json::Deserializer::from_str(student);
    let student: Student = match serde_path_to_error::deserialize(student_deserializer) {
        Ok(r) => r,
        Err(err) => {
            eprintln!("student error");

            eprintln!("{}", student);
            dbg!(err);

            panic!();
        }
    };

    let result_deserializer = &mut serde_json::Deserializer::from_str(result);
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
}

#[derive(Debug)]
pub struct StudentRecord {
    pub student: Student,
    pub result: AreaOfStudy,
    pub cells: Vec<formatter::to_record::Record>,
    pub requirement_names: Vec<String>,
    pub emphasis_requirement_names: Vec<String>,
    pub group: TableGroup,
}

impl StudentRecord {
    pub fn get_cell_by_key(&self, key: &TableKey) -> Option<&Record> {
        self.cells
            .iter()
            .find(|cell| cell.title == key.title && cell.subtitle == key.subtitle)
    }

    pub fn get_first_cell_with_key_title(&self, key: &TableKey) -> Option<&Record> {
        self.cells.iter().find(|cell| cell.title == key.title)
    }
}

#[derive(Debug, PartialEq, Hash, Eq, PartialOrd, Ord)]
struct SingleTableGroup {
    pub key: TableKey,
}

#[derive(Debug, PartialEq, Hash, Eq, PartialOrd, Ord, Clone)]
pub struct TableGroup {
    pub catalog: String,
    pub titles: Vec<TableKey>,
}

impl TableGroup {
    pub fn titles_only(&self) -> TableGroup {
        TableGroup {
            catalog: self.catalog.clone(),
            titles: self
                .titles
                .iter()
                .map(|key| key.title_only())
                .unique()
                .collect(),
        }
    }

    pub fn by_titles(&self) -> (Vec<TableKey>, String) {
        let titles_only = self.titles_only();
        (titles_only.titles.clone(), titles_only.catalog.clone())
    }
}

#[derive(Debug, PartialEq, Hash, Eq, PartialOrd, Ord, Clone, Default)]
pub struct TableKey {
    pub title: String,
    pub subtitle: Option<String>,
}

impl TableKey {
    pub fn title_only(&self) -> TableKey {
        TableKey {
            title: self.title.clone(),
            subtitle: None,
        }
    }
}

pub fn fetch_records<'a>(
    client: &'a mut postgres::Client,
    area_code: &str,
) -> anyhow::Result<Vec<StudentRecord>> {
    let mut tx = client.transaction()?;

    let options = RecordOptions {};

    // we need to know what columns each student has, so that we can generate a large-enough table.
    // 1. take the (title, subtitle) tuple from each student.
    // 2. … ignoring any requirements from emphases (/^Emphasis:/), we need to group catalog years with the same requirements together
    // 2-1. the resulting multi-catalog table should have the union of all emphasis columns.
    // 3. turn the student's row into a Mapping[(title, subtitle), CellContents].

    /*
        for column in table_headings {
            for student in all_students {
                if student in column {
                    for cell for student[column] {
                        output cell;
                    }
                }
            }
        }
    */

    let students = fetch_students(&mut tx, &area_code)?;

    tx.commit()?;

    let records = students.into_iter().map(|(student, result)| {
        let cells = result.get_row(&student, &options, false);
        let requirement_names = result.get_requirements();
        let emphasis_requirement_names = result.emphasis_requirement_names();

        let group = {
            let titles = cells
                .iter()
                // ignore any emphasis columns
                .filter(|record| !record.title.starts_with("Emphasis:"))
                .map(|record| TableKey {
                    title: record.title.clone(),
                    subtitle: record.subtitle.clone(),
                })
                .collect::<Vec<_>>();

            TableGroup {
                catalog: student.catalog.clone(),
                titles,
            }
        };

        StudentRecord {
            student,
            result,
            cells,
            requirement_names,
            emphasis_requirement_names,
            group,
        }
    });

    let mut records = records.collect::<Vec<_>>();
    records.sort_by_cached_key(|s| {
        (
            s.group.clone(),
            s.student.name_sort.clone(),
            s.student.stnum.clone(),
        )
    });
    let records = records;

    Ok(records)
}
