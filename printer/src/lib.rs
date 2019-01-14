#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::{AreaOfStudy, AreaType};
use degreepath_parser::requirement::Requirement;
use degreepath_parser::rules;
use degreepath_parser::rules::given::{action, filter};
use degreepath_parser::rules::Rule;
use std::fmt;
use std::fmt::Write;

extern crate textwrap;

pub fn print(area: AreaOfStudy) -> String {
    let mut output: Vec<String> = vec![];

    let leader = match area.area_type.clone() {
        AreaType::Degree => {
            let catalog = area.catalog;
            let area_name = area.area_name;
            let institution = "St. Olaf College";
            let area_type = "degree".to_string();
            format!("This is the set of requirements for the {catalog} “{area_name}” {area_type} from {institution}.", catalog=catalog, area_name=area_name, area_type=area_type, institution=institution)
        }
        AreaType::Major { degree } => {
            let catalog = area.catalog;
            let area_name = area.area_name;
            let institution = "St. Olaf College";
            let area_type = "major".to_string();
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog=catalog, for_degree=degree, area_name=area_name, area_type=area_type, institution=institution)
        }
        AreaType::Minor { degree } => {
            let catalog = area.catalog;
            let area_name = area.area_name;
            let institution = "St. Olaf College";
            let area_type = "minor".to_string();
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog=catalog, for_degree=degree, area_name=area_name, area_type=area_type, institution=institution)
        }
        AreaType::Concentration { degree } => {
            let catalog = area.catalog;
            let area_name = area.area_name;
            let institution = "St. Olaf College";
            let area_type = "concentration".to_string();
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog=catalog, for_degree=degree, area_name=area_name, area_type=area_type, institution=institution)
        }
        AreaType::Emphasis { degree, major } => {
            let catalog = area.catalog;
            let area_name = area.area_name;
            let institution = "St. Olaf College";
            let area_type = "area of emphasis".to_string();
            format!("This is the set of requirements for the {catalog} {for_degree} {for_major} major's “{area_name}” {area_type} from {institution}.", catalog=catalog, for_degree=degree, for_major=major, area_name=area_name, area_type=area_type, institution=institution)
        }
    };

    output.push(blockquote(&textwrap::fill(&leader, 78)));

    let area_type = match area.area_type.clone() {
        AreaType::Degree => "degree",
        AreaType::Major { .. } => "major",
        AreaType::Minor { .. } => "minor",
        AreaType::Concentration { .. } => "concentration",
        AreaType::Emphasis { .. } => "area of emphasis",
    };

    if let Ok(what_to_do) = summarize_result(&area.result) {
        output.push(textwrap::fill(
            &format!(
                "For this {area_type}, you must complete {what_to_do}",
                area_type = area_type,
                what_to_do = what_to_do
            ),
            80,
        ));

        output.push("".to_string());
    }

    let mut requirements: Vec<String> = area
        .requirements
        .iter()
        .flat_map(|(name, r)| print_requirement(name, &r.clone(), 1))
        .collect();

    output.append(&mut requirements);

    output.join("\n")
}

fn blockquote(text: &str) -> String {
    textwrap::indent(&text, "> ")
}

fn _list_item(text: &str) -> String {
    format!("- {}", text)
}

fn print_rule_as_title(rule: &Rule) -> Result<String, fmt::Error> {
    match rule {
        Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
            Ok(format!("“{}”", requirement))
        }
        Rule::Course(rules::course::Rule { course, .. }) => Ok(course.to_string()),
        Rule::Either(rules::either::Rule { either: pair })
        | Rule::Both(rules::both::Rule { both: pair }) => {
            let a = summarize_result(&pair.0.clone())?;
            let b = summarize_result(&pair.1.clone())?;
            Ok(format!("{}, {}", a, b))
        }
        Rule::Given(rules::given::Rule { .. }) => Ok("given blah".to_string()),
        Rule::Do(rules::action::Rule { .. }) => Ok("do blah".to_string()),
        Rule::CountOf(rules::count_of::Rule { of, count }) => Ok(format!(
            "{} {}",
            count,
            of.iter()
                .map(|r| print_rule_as_title(&r.clone()).unwrap_or("error!!!".to_string()))
                .collect::<Vec<String>>()
                .join(" • ")
        )),
    }
}

fn print_requirement(name: &str, req: &Requirement, level: usize) -> Vec<String> {
    let mut output: Vec<String> = vec![];

    output.push(format!("{} {}", "#".repeat(level), name));

    if let Some(message) = &req.message {
        let message = format!("Note: {}", message);
        output.push(blockquote(&textwrap::fill(&message, 78)));
        output.push("".to_string());
    }

    if let Some(result) = &req.result {
        if let Ok(what_to_do) = summarize_result(&result) {
            let kind = match req.requirements.len() {
                0 => "requirement",
                _ => "section",
            };

            output.push(textwrap::fill(
                &format!(
                    "For this {kind}, you must {what_to_do}",
                    kind = kind,
                    what_to_do = what_to_do
                ),
                80,
            ));

            output.push("".to_string());
        }
    }

    let mut requirements: Vec<String> = req
        .requirements
        .iter()
        .flat_map(|(name, r)| print_requirement(name, &r.clone(), level + 1))
        .collect();

    output.append(&mut requirements);

    output
}

fn summarize_result(rule: &Rule) -> Result<String, fmt::Error> {
    let mut w = String::new();

    match rule {
        Rule::CountOf(rules::count_of::Rule { of, .. }) => {
            let all_are_requirements = of.iter().all(|rule| match rule {
                Rule::Requirement { .. } => true,
                _ => false,
            });

            if all_are_requirements {
                let requirement_names: Vec<String> = of
                    .iter()
                    .map(|r| print_rule_as_title(&r.clone()).unwrap_or("error!!!".to_string()))
                    .collect();

                let names = oxford(requirement_names.as_slice());

                match requirement_names.len() {
                    0 => write!(&mut w, "… do nothing.")?,
                    1 => write!(&mut w, "complete the {} requirement.", names)?,
                    2 => write!(&mut w, "complete both the {} requirements.", names)?,
                    _ => write!(&mut w, "complete all of the {} requirements.", names)?,
                };
            } else {
                println!("{:?}", rule);
                panic!("count-of rule had non-requirements in it")
            }
        }
        Rule::Course(rules::course::Rule { course, .. }) => {
            write!(&mut w, "{}", course.to_string())?;
        }
        Rule::Either(rules::either::Rule { either: pair })
        | Rule::Both(rules::both::Rule { both: pair }) => {
            let a = summarize_result(&pair.0.clone())?;
            let b = summarize_result(&pair.1.clone())?;
            write!(&mut w, "{}, {}", a, b)?;
        }
        Rule::Given(rules::given::Rule {
            given,
            action,
            what,
            filter,
            ..
        }) => match given {
            rules::given::Given::AreasOfStudy => match what {
                rules::given::What::AreasOfStudy => match action {
                    action::Action {
                        lhs: action::Value::Command(action::Command::Count),
                        op: Some(action::Operator::GreaterThanEqualTo),
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => describe_areas_filter(f),
                            None => "".into(),
                        };

                        let count = match rhs {
                            action::Value::Integer(1) => "one",
                            _ => panic!("unknown number"),
                        };

                        // For this requirement, you must also complete one "major".
                        write!(&mut w, "also complete {} {}.", count, filter_desc)?;
                    }
                    _ => panic!("unimplemented"),
                },
                _ => panic!("given: areas, what: !areas???"),
            },
            rules::given::Given::AllCourses => match what {
                rules::given::What::Credits => match action {
                    action::Action {
                        lhs: action::Value::Command(action::Command::Sum),
                        op: Some(action::Operator::GreaterThanEqualTo),
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => describe_courses_filter(f),
                            None => "".into(),
                        };

                        write!(
                            &mut w,
                            "complete enough courses{} to obtain {} credits.",
                            filter_desc, rhs
                        )?;
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        write!(&mut w, "given blah")?;
                    }
                },
                rules::given::What::DistinctCourses => match action {
                    action::Action {
                        lhs: action::Value::Command(action::Command::Count),
                        op,
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => describe_courses_filter(f),
                            None => "".into(),
                        };

                        let counter = match op {
                            Some(action::Operator::GreaterThanEqualTo) => "at least",
                            _ => panic!("other actions for {given: courses, what: courses} are not implemented yet")
                        };

                        let course_word = match rhs {
                            action::Value::Integer(n) if *n == 1 => "course",
                            action::Value::Float(n) if *n == 1.0 => "course",
                            _ => "courses",
                        };

                        write!(
                            &mut w,
                            "complete {counter} {num} distinct {word}{desc}.",
                            counter = counter,
                            num = rhs,
                            word = course_word,
                            desc = filter_desc
                        )?;
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        write!(&mut w, "given blah")?;
                    }
                },
                rules::given::What::Courses => match action {
                    action::Action {
                        lhs: action::Value::Command(action::Command::Count),
                        op,
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => describe_courses_filter(f),
                            None => "".into(),
                        };

                        let counter = match op {
                            Some(action::Operator::GreaterThanEqualTo) => "at least",
                            _ => panic!("other actions for {given: courses, what: courses} are not implemented yet")
                        };

                        let course_word = match rhs {
                            action::Value::Integer(n) if *n == 1 => "course",
                            action::Value::Float(n) if *n == 1.0 => "course",
                            _ => "courses",
                        };

                        write!(
                            &mut w,
                            "complete {counter} {num} {word}{desc}.",
                            counter = counter,
                            num = rhs,
                            word = course_word,
                            desc = filter_desc
                        )?;
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        write!(&mut w, "given blah")?;
                    }
                },
                rules::given::What::Grades => match action {
                    action::Action {
                        lhs: action::Value::Command(action::Command::Average),
                        op: Some(op),
                        rhs: Some(rhs),
                    } => match op {
                        action::Operator::GreaterThanEqualTo => {
                            write!(
                                &mut w,
                                "maintain a {} or greater GPA across all of your courses.",
                                rhs
                            )?;
                        }
                        action::Operator::GreaterThan => {
                            write!(
                                &mut w,
                                "maintain a GPA above {} across all of your courses.",
                                rhs
                            )?;
                        }
                        action::Operator::EqualTo => {
                            write!(
                                &mut w,
                                "maintain exactly a {} GPA across all of your courses.",
                                rhs
                            )?;
                        }
                        action::Operator::NotEqualTo => {
                            panic!("not equal to makes no sense here");
                        }
                        action::Operator::LessThan => {
                            write!(
                                &mut w,
                                "maintain less than a {} GPA across all of your courses.",
                                rhs
                            )?;
                        }
                        action::Operator::LessThanEqualTo => {
                            write!(
                                &mut w,
                                "maintain at most a {} GPA across all of your courses.",
                                rhs
                            )?;
                        }
                    },
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        write!(&mut w, "given blah")?;
                    }
                },
                _ => {
                    println!("{:?}", given);
                    println!("{:?}", action);
                    write!(&mut w, "given blah")?;
                }
            },
            _ => {
                println!("{:?}", given);
                println!("{:?}", action);
                write!(&mut w, "given blah")?;
            }
        },
        Rule::Do(rules::action::Rule { .. }) => {
            write!(&mut w, "do blah")?;
        }
        Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
            write!(&mut w, "requirement {} blah", requirement)?;
        }
    };

    Ok(w)
}

fn oxford(v: &[String]) -> String {
    match v.len() {
        0 => "".to_string(),
        1 => v[0].to_string(),
        2 => v.join(" and "),
        _ => match v.split_last() {
            Some((last, others)) => format!("{}, and {}", others.join(", "), last),
            _ => panic!("v's len() was > 2, but there weren't two items in it"),
        },
    }
}

fn describe_courses_filter(filter: &filter::Clause) -> String {
    let clauses: Vec<String> = filter
        .iter()
        .map(|(k, v)| match v {
            filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::EqualTo,
                value,
            }) => match k.as_ref() {
                "institution" => format!(" at {}", value),
                "level" => format!(" at the {} level", value),
                "gereqs" => format!(" with the {} general education attribute", value),
                "graded" => {
                    if v.is_true() {
                        ", graded,".into()
                    } else {
                        ", non-graded,".into()
                    }
                }
                _ => format!(" blargh filter key={}", k),
            },
            filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::GreaterThanEqualTo,
                value,
            }) => match k.as_ref() {
                "level" => format!(" at or above the {} level", value),
                _ => format!(" blargh filter key={}", k),
            },
            _ => format!(" blargh other filter value type"),
        })
        .collect();

    oxford(clauses.as_slice())
}

fn describe_areas_filter(filter: &filter::Clause) -> String {
    let clauses: Vec<String> = filter
        .iter()
        .map(|(k, v)| match v {
            filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::EqualTo,
                value,
            }) => match k.as_ref() {
                "type" => format!("{}", value),
                _ => format!(" blargh filter key={}", k),
            },
            _ => format!(" blargh other filter value type"),
        })
        .collect();

    oxford(clauses.as_slice())
}

#[cfg(test)]
mod tests {
    // use super::*;

    // #[test]
    // fn print_top_level() {
    //     let input = AreaOfStudy {
    //
    //     }
    // }
}
