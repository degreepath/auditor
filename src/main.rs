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

    let area: AreaOfStudy = serde_yaml::from_str(&contents).unwrap();

    println!("{}", serde_yaml::to_string(&area).unwrap());

    // let value: serde_yaml::Value = serde_yaml::from_str(&contents).unwrap();
    // match parse(&value) {
    //     Ok(area) => println!("{}", serde_yaml::to_string(&area).unwrap()),
    //     Err(error) => println!("{:?}", error),
    // }
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

    let requirements = match contents.get("requirements") {
        Some(value) => match value.as_mapping() {
            Some(v) => v
                .iter()
                .map(|(k, v)| {
                    (
                        k.as_str().unwrap().to_string(),
                        parse_requirement(v).unwrap(),
                    )
                })
                .collect::<HashMap<String, requirement::Requirement>>(),
            None => return Err(ParseError::InvalidValueType("`requirements`".to_string())),
        },
        None => return Err(ParseError::MissingKey("`requirements`".to_string())),
    };

    return Ok(AreaOfStudy {
        area_name,
        area_type,
        for_degree,
        catalog,
        requirements,
        result,
    });
}

fn parse_requirement(contents: &serde_yaml::Value) -> Result<requirement::Requirement, ParseError> {
    if !contents.is_mapping() {
        return Err(ParseError::InvalidValueType("`requirement`".to_string()));
    }

    let result = match contents.get(&yaml_key("result")) {
        Some(v) => match parse_result(v) {
            Ok(v) => Some(v),
            Err(err) => return Err(err),
        },
        None => return Err(ParseError::MissingKey("`result`".to_string())),
    };

    return Ok(requirement::Requirement {
        result,
        contract: false,
        department_audited: false,
        message: None,
        requirements: HashMap::new(),
        save: vec![],
    });
}

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

fn yaml_key<'a>(name: &'a str) -> serde_yaml::Value {
    serde_yaml::Value::String(name.to_string())
}

fn parse_rule(contents: &serde_yaml::Value) -> Result<rules::Rule, ParseError> {
    // result: DEPT 111
    if let Some(course) = contents.as_str() {
        return match course.parse::<rules::course::CourseRule>() {
            Ok(course) => Ok(rules::Rule::Course(course)),
            Err(_) => Err(ParseError::InvalidValueType("`course`".to_string())),
        };
    }

    let mapping: serde_yaml::Mapping;
    match contents.as_mapping() {
        Some(m) => mapping = m.clone(),
        None => return Err(ParseError::InvalidValueType("`result`".to_string())),
    }

    let keys: Vec<&str> = mapping
        .iter()
        .filter_map(|(key, _value)| key.as_str())
        .collect();

    // result: {course: DEPT 111}
    if let Some(rule) = mapping.get(&yaml_key("course")) {
        let course: String;
        match rule.as_str() {
            Some(val) => course = val.to_string(),
            None => return Err(ParseError::InvalidValueType("`course`".to_string())),
        };

        // if it's just the {course: DEPT 111} style
        if keys.len() == 1 {
            return match course.parse::<rules::course::CourseRule>() {
                Ok(course) => Ok(rules::Rule::Course(course)),
                Err(_) => Err(ParseError::InvalidValueType("`course`".to_string())),
            };
        }

        // otherwise, we need to pull out the other keys that might be offered
        let international = mapping
            .get(&yaml_key("international"))
            .and_then(|v| v.as_bool());

        let lab = mapping.get(&yaml_key("lab")).and_then(|v| v.as_bool());

        let section = mapping
            .get(&yaml_key("section"))
            .and_then(|v| v.as_str())
            .map(|v| v.to_string());

        let semester = mapping
            .get(&yaml_key("semester"))
            .and_then(|v| v.as_str())
            .map(|v| v.to_string());

        let year = mapping.get(&yaml_key("year")).and_then(|v| v.as_u64());

        let term = mapping
            .get(&yaml_key("year"))
            .and_then(|v| v.as_str())
            .map(|v| v.to_string());

        return Ok(rules::Rule::Course(rules::course::CourseRule {
            course,
            international,
            lab,
            section,
            semester,
            year,
            term,
        }));
    }

    // result: {both: [course: DEPT 111, course: DEPT 122]}
    if let Some(rule) = mapping.get(&yaml_key("both")) {
        let halves: Result<Vec<rules::Rule>, ParseError> = match rule.as_sequence() {
            Some(seq) => seq.iter().map(|v| parse_rule(v)).collect(),
            None => return Err(ParseError::InvalidValueType("`both`".to_string())),
        };

        let a: rules::Rule;
        let b: rules::Rule;
        match halves {
            Ok(values) => match values.len() == 2 {
                true => {
                    a = values[0].clone();
                    b = values[1].clone();
                }
                false => return Err(ParseError::InvalidValueType("`both`".to_string())),
            },
            Err(_err) => return Err(ParseError::InvalidValueType("`both`".to_string())),
        };

        return Ok(rules::Rule::Both(rules::both::BothRule {
            both: (Box::new(a), Box::new(b)),
        }));
    }

    // result: {either: [course: DEPT 111, course: DEPT 122]}
    if let Some(rule) = mapping.get(&yaml_key("either")) {
        let halves: Result<Vec<rules::Rule>, ParseError> = match rule.as_sequence() {
            Some(seq) => seq.iter().map(|v| parse_rule(v)).collect(),
            None => return Err(ParseError::InvalidValueType("`either`".to_string())),
        };

        let a: rules::Rule;
        let b: rules::Rule;
        match halves {
            Ok(values) => match values.len() == 2 {
                true => {
                    a = values[0].clone();
                    b = values[1].clone();
                }
                false => return Err(ParseError::InvalidValueType("`either`".to_string())),
            },
            Err(_err) => return Err(ParseError::InvalidValueType("`either`".to_string())),
        };

        return Ok(rules::Rule::Either(rules::either::EitherRule {
            either: (Box::new(a), Box::new(b)),
        }));
    }

    // result: {requirement: FOO, optional: false}
    if let Some(rule) = mapping.get(&yaml_key("requirement")) {
        let requirement: String;
        match rule.as_str() {
            Some(val) => requirement = val.to_string(),
            None => return Err(ParseError::InvalidValueType("`requirement`".to_string())),
        };

        let optional = mapping
            .get(&yaml_key("optional"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);

        return Ok(rules::Rule::Requirement(
            rules::requirement::RequirementRule {
                requirement,
                optional,
            },
        ));
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

// impl From<std::option::NoneError> for ParseError {
//     fn from(item: std::option::NoneError) -> ParseError {
//         ParseError::MissingKey("missing".to_string())
//     }
// }
