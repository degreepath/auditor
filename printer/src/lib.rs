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

    if let Some(result) = &req.result {
        let what_to_do = summarize_result(&result);

        output.push(textwrap::fill(
            &format!(
                "For this requirement, you must complete {what_to_do}",
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
    // For this degree, you must complete both the "Degree Requirements" and "General Education" sections.

    match rule {
        Rule::CountOf(rules::count_of::Rule { of, .. }) => {
            let requirement_names: Vec<String> = of
                .iter()
                .map(|rule| print_rule_as_title(&rule.clone()))
                .collect();

            match requirement_names.len() {
                0 => "… nothing.".to_string(),
                1 => format!("the {} requirement.", requirement_names.join("")),
                2 => format!("both the {} requirements.", requirement_names.join(" and ")),
                _ => {
                    if let Some((last, others)) = requirement_names.clone().split_last() {
                        let others = others.join(", ");
                        format!("all of the {}, and {} requirements.", others, last)
                    } else {
                        panic!("no requirements?");
                    }
                }
            }
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
        Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
            format!("requirement {} blah", requirement)
        }
    }
}

#[cfg(test)]
mod tests {}
