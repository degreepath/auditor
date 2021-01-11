use crate::structs::MappedResult;
use formatter::area_of_study::AreaOfStudy;
use formatter::student::{AreaOfStudy as AreaPointer, Emphasis, Student};
use formatter::to_cell::{CsvOptions, ToCell};
use serde_path_to_error;
use std::collections::BTreeSet;

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

pub fn fetch_records(
    client: &mut postgres::Client,
    area_code: &str,
) -> anyhow::Result<Vec<MappedResult>> {
    let mut tx = client.transaction()?;

    let options = CsvOptions {};

    let results = fetch_students(&mut tx, &area_code)?
        .into_iter()
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
            (
                s.catalog.clone(),
                s.emphases.join(","),
                s.name.clone(),
                s.stnum.clone(),
            )
        });

        r
    };

    Ok(results)
}
