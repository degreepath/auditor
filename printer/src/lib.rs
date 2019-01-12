#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::{AreaOfStudy, AreaType};
use degreepath_parser::rules;
use degreepath_parser::rules::Rule;

extern crate textwrap;

/*
> This is the set of requirements for the 2015-16 "Bachelor of Arts" degree from
> St. Olaf College.

For this degree, you must complete both the "Degree Requirements" and "General
Education" sections.

# Degree Requirements

For this section, you must complete all of the "Courses", "Residency", "Interim",
"Grade Point Average", "Course Level", "Graded Courses", and "Major"
requirements.

## Courses
For this requirement, you must complete enough courses to obtain 35 credits.

## Residency
For this requirement, you must complete enough courses at St. Olaf College to
obtain 17 credits.
*/

pub fn print(area: AreaOfStudy) -> String {
    let mut output = "".to_string();

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

    output += &blockquote(&textwrap::fill(&leader, 78));
    output += "\n";

    let area_type = match area.area_type.clone() {
        AreaType::Degree => "degree",
        AreaType::Major { .. } => "major",
        AreaType::Minor { .. } => "minor",
        AreaType::Concentration { .. } => "concentration",
        AreaType::Emphasis { .. } => "area of emphasis",
    };

    // For this degree, you must complete both the "Degree Requirements" and "General Education" sections.

    let what_to_do: String;

    match area.result {
        Rule::CountOf(rules::count_of::Rule { of, .. }) => {
            let requirement_names: Vec<String> = of
                .iter()
                .map(|rule| print_rule_as_title(&rule.clone()))
                .collect();

            // let requirement_names: Vec<String> =
            //     area.result.keys().map(|n| format!("“{}”", n)).collect();

            what_to_do = match requirement_names.len() {
                0 => "… nothing.".to_string(),
                1 => format!("the {} requirement.", requirement_names.join("")),
                2 => format!("both the {} requirements.", requirement_names.join(" and ")),
                _ => {
                    // For this section, you must complete all of the "Courses",
                    // "Residency", "Interim", "Grade Point Average", "Course Level",
                    // "Graded Courses", and "Major" requirements.
                    if let Some((last, others)) = requirement_names.clone().split_last() {
                        format!(
                            "all of the {}, and {} requirements.",
                            others.join(", "),
                            last
                        )
                    } else {
                        panic!("no requirements?");
                    }
                }
            };
        }
        _ => panic!("not implented yet!"),
    }

    output += &textwrap::fill(
        &format!(
            "For this {area_type}, you must complete {what_to_do}",
            area_type = area_type,
            what_to_do = what_to_do
        ),
        80,
    );

    output
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
        _ => panic!("not implented yet!"),
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
