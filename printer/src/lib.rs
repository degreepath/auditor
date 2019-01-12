extern crate degreepath_parser;
use degreepath_parser::area_of_study::{AreaOfStudy, AreaType};

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

    output += &blockquote(textwrap::fill(&leader, 78));
    output += "\n";

    let area_type = match area.area_type.clone() {
        AreaType::Degree => "degree",
        AreaType::Major { degree: _ } => "major",
        AreaType::Minor { degree: _ } => "minor",
        AreaType::Concentration { degree: _ } => "concentration",
        AreaType::Emphasis {
            degree: _,
            major: _,
        } => "area of emphasis",
    };

    // For this degree, you must complete both the "Degree Requirements" and "General Education" sections.

    let requirement_names: Vec<String> = area
        .requirements
        .keys()
        .map(|n| format!("“{}”", n))
        .collect();

    let what_to_do: String = match requirement_names.len() {
        0 => "… nothing.".to_string(),
        1 => format!("the {} requirement.", requirement_names.join("")),
        2 => format!("both the {} requirements.", requirement_names.join(" and ")),
        _ => {
            let names_as_list: Vec<String> = requirement_names
                .iter()
                .map(|n| format!("- {}", n))
                .collect();
            format!("all of these requirements:\n\n{}", names_as_list.join("\n"))
        }
    };

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

fn blockquote(text: String) -> String {
    textwrap::indent(&text, "> ")
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
