use crate::structs::MappedResult;
use formatter::area_of_study::AreaOfStudy;
use formatter::student::{AreaOfStudy as AreaPointer, Emphasis, Student};
use formatter::to_csv::{CsvOptions, ToCsv};
use itertools::Itertools;
use serde_path_to_error;
use std::collections::{BTreeMap, BTreeSet, HashMap};

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
