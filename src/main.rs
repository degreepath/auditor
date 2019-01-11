use std::collections::HashMap;
use std::env;
use std::fs;

extern crate gobbldygook_area_auditor;
extern crate serde_yaml;

use gobbldygook_area_auditor::{area_of_study::AreaOfStudy, requirement, rules, save::SaveBlock};

fn main() {
    let args: Vec<String> = env::args().collect();
    let filename = &args[1];

    let contents = fs::read_to_string(filename).expect(&format!(
        "Something went wrong reading the file `{}`",
        filename
    ));

    // println!("With text:\n{}", contents);

    // let actual: AreaOfStudy = serde_yaml::from_str(&contents).unwrap();

    let value: serde_yaml::Value = serde_yaml::from_str(&contents).unwrap();
    match parse(&value) {
        Ok(area) => println!("{}", serde_yaml::to_string(&area).unwrap()),
        Err(error) => println!("{:?}", error),
    }
}

fn parse(contents: &serde_yaml::Value) -> Result<AreaOfStudy, ParseError> {
    let area_name = match contents.get("name") {
        Some(value) => match value.as_str() {
            Some(v) => v.to_string(),
            None => return Err(ParseError::InvalidValueType("`name`".to_string())),
        },
        None => return Err(ParseError::MissingKey("`name`".to_string())),
    };

    let area_type = match contents.get("type") {
        Some(value) => match value.as_str() {
            Some(v) => v.to_string(),
            None => return Err(ParseError::InvalidValueType("`type`".to_string())),
        },
        None => return Err(ParseError::MissingKey("`type`".to_string())),
    };

    if area_type != area_type.to_lowercase() {
        return Err(ParseError::InvalidValue(
            "`type` is not lowercase".to_string(),
        ));
    }

    let for_degree = match contents.get("degree") {
        Some(value) => match value.as_str() {
            Some(v) => v.to_string(),
            None => return Err(ParseError::InvalidValueType("`degree`".to_string())),
        },
        None => return Err(ParseError::MissingKey("`degree`".to_string())),
    };

    let catalog = match contents.get("catalog") {
        Some(value) => match value.as_str() {
            Some(v) => v.to_string(),
            None => return Err(ParseError::InvalidValueType("`catalog`".to_string())),
        },
        None => return Err(ParseError::MissingKey("`catalog`".to_string())),
    };

    let result = match contents.get("result") {
        Some(value) => match parse_result(value) {
            Ok(v) => v,
            Err(e) => return Err(e),
        },
        None => return Err(ParseError::MissingKey("`result`".to_string())),
    };

    return Ok(AreaOfStudy {
        area_name,
        area_type,
        for_degree,
        catalog,
        requirements: HashMap::new(),
        result,
    });
}

// fn parse_requirement(contents: &str) -> Requirement {
// }

fn parse_result(contents: &serde_yaml::Value) -> Result<rules::Rule, ParseError> {
    // cannot turn string into course as the only thing in a result; use `course: DEPT 111` instead.
    if let Some(_) = contents.as_str() {
        return Err(ParseError::InvalidValueType("`result`".to_string()));
    }

    match contents.is_mapping() {
        true => parse_rule(contents),
        false => Err(ParseError::InvalidValueType("`result`".to_string())),
    }
}

fn parse_rule(contents: &serde_yaml::Value) -> Result<rules::Rule, ParseError> {
    // result: DEPT 111
    if let Some(course_str) = contents.as_str() {
        return match course_str.parse::<rules::course::CourseRule>() {
            Ok(course) => Ok(rules::Rule::Course(course)),
            Err(_) => Err(ParseError::InvalidValueType("`course`".to_string())),
        };
    }

    // result: {course: DEPT 111}
    if let Some(rule) = contents.get("course") {
        if let Some(course_str) = rule.as_str() {
            return match course_str.parse::<rules::course::CourseRule>() {
                Ok(course) => Ok(rules::Rule::Course(course)),
                Err(_) => Err(ParseError::InvalidValueType("`course`".to_string())),
            };
        }
    }

    return Ok(rules::Rule::Requirement(
        rules::requirement::RequirementRule {
            requirement: "blarg".to_string(),
            optional: false,
        },
    ));
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    MissingKey(String),
    InvalidValueType(String),
    InvalidValue(String),
}
