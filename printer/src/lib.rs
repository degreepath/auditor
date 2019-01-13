#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::{AreaOfStudy, AreaType};
use degreepath_parser::requirement::Requirement;
use degreepath_parser::rules;
use degreepath_parser::rules::Rule;

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

    let what_to_do = summarize_result(&area.result);

    output.push(textwrap::fill(
        &format!(
            "For this {area_type}, you must complete {what_to_do}",
            area_type = area_type,
            what_to_do = what_to_do
        ),
        80,
    ));

    output.push("".to_string());

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

fn print_rule_as_title(rule: &Rule) -> String {
    match rule {
        Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
            format!("“{}”", requirement)
        }
        Rule::Course(rules::course::Rule { course, .. }) => course.to_string(),
        Rule::Either(rules::either::Rule { either: pair })
        | Rule::Both(rules::both::Rule { both: pair }) => {
            let a = summarize_result(&pair.0.clone());
            let b = summarize_result(&pair.1.clone());
            format!("{}, {}", a, b)
        }
        Rule::Given(rules::given::Rule { .. }) => "given blah".to_string(),
        Rule::Do(rules::action::Rule { .. }) => "do blah".to_string(),
        Rule::CountOf(rules::count_of::Rule { of, count }) => format!(
            "{} {}",
            count,
            of.iter()
                .map(|r| print_rule_as_title(&r.clone()))
                .collect::<Vec<String>>()
                .join("•")
        ),
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
        let what_to_do = summarize_result(&result);

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

    let mut requirements: Vec<String> = req
        .requirements
        .iter()
        .flat_map(|(name, r)| print_requirement(name, &r.clone(), level + 1))
        .collect();

    output.append(&mut requirements);

    output
}

fn summarize_result(rule: &Rule) -> String {
    match rule {
        Rule::CountOf(rules::count_of::Rule { of, .. }) => {
            let all_are_requirements = of.iter().all(|rule| match rule {
                Rule::Requirement { .. } => true,
                _ => false,
            });

            if all_are_requirements {
                let requirement_names: Vec<String> = of
                    .iter()
                    .map(|rule| print_rule_as_title(&rule.clone()))
                    .collect();

                match requirement_names.len() {
                    0 => "… do nothing.".to_string(),
                    1 => format!("complete the {} requirement.", requirement_names.join("")),
                    2 => format!(
                        "complete both the {} requirements.",
                        requirement_names.join(" and ")
                    ),
                    _ => {
                        if let Some((last, others)) = requirement_names.clone().split_last() {
                            let others = others.join(", ");
                            format!("complete all of the {}, and {} requirements.", others, last)
                        } else {
                            panic!("… er, there are no requirements?");
                        }
                    }
                }
            } else {
                println!("{:?}", rule);
                panic!("count-of rule had non-requirements in it")
            }
        }
        Rule::Course(rules::course::Rule { course, .. }) => course.to_string(),
        Rule::Either(rules::either::Rule { either: pair })
        | Rule::Both(rules::both::Rule { both: pair }) => {
            let a = summarize_result(&pair.0.clone());
            let b = summarize_result(&pair.1.clone());
            format!("{}, {}", a, b)
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
                    rules::given::action::Action {
                        lhs:
                            rules::given::action::Value::Command(rules::given::action::Command::Count),
                        op: Some(rules::given::action::Operator::GreaterThanEqualTo),
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => {
                                // TODO: handle multiple filter conditions
                                if let Some(val) = f.get("type") {
                                    format!("{}", val)
                                } else {
                                    "".into()
                                }
                            }
                            None => "".into(),
                        };

                        let count = match rhs {
                            rules::given::action::Value::Integer(1) => "one",
                            _ => panic!("unknown number"),
                        };

                        // For this requirement, you must also complete one "major".
                        format!("also complete {} {}.", count, filter_desc)
                    }
                    _ => panic!("unimplemented"),
                },
                _ => panic!("given: areas, what: !areas???"),
            },
            rules::given::Given::AllCourses => match what {
                rules::given::What::Credits => match action {
                    rules::given::action::Action {
                        lhs:
                            rules::given::action::Value::Command(rules::given::action::Command::Sum),
                        op: Some(rules::given::action::Operator::GreaterThanEqualTo),
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => {
                                // TODO: handle multiple filter conditions
                                if let Some(val) = f.get("institution") {
                                    format!(" at {}", val)
                                } else if let Some(val) = f.get("level") {
                                    // TODO: fix this "at or above"; it's actually determined through the value here, not the action's operator
                                    format!(" TODO at the {} level", val)
                                } else if let Some(val) = f.get("graded") {
                                    if val.is_true() {
                                        ", graded,".into()
                                    } else {
                                        ", non-graded,".into()
                                    }
                                } else {
                                    "".into()
                                }
                            }
                            None => "".into(),
                        };
                        format!(
                            "complete enough courses{} to obtain {} credits.",
                            filter_desc, rhs
                        )
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        "given blah".to_string()
                    }
                },
                rules::given::What::DistinctCourses => match action {
                    rules::given::action::Action {
                        lhs:
                            rules::given::action::Value::Command(rules::given::action::Command::Count),
                        op,
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => {
                                // TODO: handle multiple filter conditions
                                if let Some(val) = f.get("institution") {
                                    format!(" at {}", val)
                                } else if let Some(val) = f.get("gereqs") {
                                    format!(" with the {} general education attribute", val)
                                } else if let Some(val) = f.get("level") {
                                    format!(" at or above the {} level", val)
                                } else if let Some(val) = f.get("graded") {
                                    if val.is_true() {
                                        ", graded,".into()
                                    } else {
                                        ", non-graded,".into()
                                    }
                                } else {
                                    "".into()
                                }
                            }
                            None => "".into(),
                        };

                        let counter = match op {
                            Some(rules::given::action::Operator::GreaterThanEqualTo) => "at least",
                            _ => panic!("other actions for {given: courses, what: courses} are not implemented yet")
                        };

                        let course_word = match rhs {
                            rules::given::action::Value::Integer(n) if *n == 1 => "course",
                            rules::given::action::Value::Float(n) if *n == 1.0 => "course",
                            _ => "courses",
                        };

                        format!(
                            "complete {counter} {num} distinct {word}{desc}.",
                            counter = counter,
                            num = rhs,
                            word = course_word,
                            desc = filter_desc
                        )
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        "given blah".to_string()
                    }
                },
                rules::given::What::Courses => match action {
                    rules::given::action::Action {
                        lhs:
                            rules::given::action::Value::Command(rules::given::action::Command::Count),
                        op,
                        rhs: Some(rhs),
                    } => {
                        let filter_desc = match filter {
                            Some(f) => {
                                // TODO: handle multiple filter conditions
                                if let Some(val) = f.get("institution") {
                                    format!(" at {}", val)
                                } else if let Some(val) = f.get("gereqs") {
                                    format!(" with the {} general education attribute", val)
                                } else if let Some(val) = f.get("level") {
                                    format!(" at or above the {} level", val)
                                } else if let Some(val) = f.get("graded") {
                                    if val.is_true() {
                                        ", graded,".into()
                                    } else {
                                        ", non-graded,".into()
                                    }
                                } else {
                                    "".into()
                                }
                            }
                            None => "".into(),
                        };

                        let counter = match op {
                            Some(rules::given::action::Operator::GreaterThanEqualTo) => "at least",
                            _ => panic!("other actions for {given: courses, what: courses} are not implemented yet")
                        };

                        let course_word = match rhs {
                            rules::given::action::Value::Integer(n) if *n == 1 => "course",
                            rules::given::action::Value::Float(n) if *n == 1.0 => "course",
                            _ => "courses",
                        };

                        format!(
                            "complete {counter} {num} {word}{desc}.",
                            counter = counter,
                            num = rhs,
                            word = course_word,
                            desc = filter_desc
                        )
                    }
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        "given blah".to_string()
                    }
                },
                rules::given::What::Grades => match action {
                    rules::given::action::Action {
                        lhs:
                            rules::given::action::Value::Command(rules::given::action::Command::Average),
                        op: Some(op),
                        rhs: Some(rhs),
                    } => match op {
                        rules::given::action::Operator::GreaterThanEqualTo => format!(
                            "maintain a {} or greater GPA across all of your courses.",
                            rhs
                        ),
                        rules::given::action::Operator::GreaterThan => {
                            format!("maintain a GPA above {} across all of your courses.", rhs)
                        }
                        rules::given::action::Operator::EqualTo => {
                            format!("maintain exactly a {} GPA across all of your courses.", rhs)
                        }
                        rules::given::action::Operator::NotEqualTo => {
                            panic!("not equal to makes no sense here")
                        }
                        rules::given::action::Operator::LessThan => format!(
                            "maintain less than a {} GPA across all of your courses.",
                            rhs
                        ),
                        rules::given::action::Operator::LessThanEqualTo => {
                            format!("maintain at most a {} GPA across all of your courses.", rhs)
                        }
                    },
                    _ => {
                        println!("{:?}", given);
                        println!("{:?}", action);
                        "given blah".to_string()
                    }
                },
                _ => {
                    println!("{:?}", given);
                    println!("{:?}", action);
                    "given blah".to_string()
                }
            },
            _ => {
                println!("{:?}", given);
                println!("{:?}", action);
                "given blah".to_string()
            }
        },
        Rule::Do(rules::action::Rule { .. }) => "do blah".to_string(),
        Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
            format!("requirement {} blah", requirement)
        }
    }
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
