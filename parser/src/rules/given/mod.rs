use crate::rules::{course, requirement};
use crate::util::{self, Oxford};

pub mod action;
pub mod filter;
pub mod limit;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(flatten)]
    pub given: Given,
    #[serde(default)]
    pub limit: Option<Vec<limit::Limiter>>,
    #[serde(
        rename = "where",
        default,
        deserialize_with = "filter::deserialize_with"
    )]
    pub filter: Option<filter::Clause>,
    pub what: What,
    #[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
    pub action: action::Action,
}

impl crate::rules::traits::PrettyPrint for Rule {
    fn print(&self) -> Result<String, std::fmt::Error> {
        use std::fmt::Write;

        let mut output = String::new();

        let filter = match &self.filter {
            Some(f) => format!(" {}", f.print()?),
            None => "".to_string(),
        };


        match &self.given {
            Given::AllCourses => match &self.what {
                What::Courses => {
                    let word = if self.action.should_pluralize() {"courses"} else {"course"};
                    write!(&mut output, "{} {}{}", self.action.print()?, word, filter)?;
                }
                What::DistinctCourses => {
                    let word = if self.action.should_pluralize() {"distinct courses"} else {"course"};
                    write!(&mut output, "{} {}{}", self.action.print()?, word, filter)?;
                }
                What::Credits => {
                    let word = if self.action.should_pluralize() {"credits"} else {"credit"};
                    write!(&mut output, "enough courses{} to obtain {} {}", filter, self.action.print()?, word)?;
                }
                What::Departments => {
                    let word = if self.action.should_pluralize() {"departments"} else {"department"};
                    write!(&mut output, "enough courses{} to span {} {}", filter, self.action.print()?, word)?;
                }
                What::Grades => {
                    let word = if self.action.should_pluralize() {"courses"} else {"course"};
                    write!(&mut output, "maintain an average GPA {} from {}{}", self.action.print()?, word, filter)?;
                }
                What::Terms => {
                    let word = if self.action.should_pluralize() {"terms"} else {"term"};
                    write!(&mut output, "enough courses{} to span {} {}", filter, self.action.print()?, word)?;
                }
                _ => unimplemented!(),
            },
            Given::TheseCourses {
                courses,
                repeats: mode,
            } => match (mode, &self.what) {
                (RepeatMode::First, What::Courses) => {
                    // TODO: expose last vs. first in output somehow?
                    let courses = courses.iter().map(|r| r.print().unwrap()).collect::<Vec<String>>().oxford("and");
                    write!(&mut output, "{}", courses)?;
                }
                (RepeatMode::Last, What::Courses) => {
                    // TODO: expose last vs. first in output somehow?
                    let courses = courses.iter().map(|r| r.print().unwrap()).collect::<Vec<String>>().oxford("and");
                    write!(&mut output, "{}", courses)?;
                }
                (RepeatMode::All, What::Courses) => {
                    // TODO: special-case "once" and "twice"
                    let courses = courses.iter().map(|r| r.print().unwrap()).collect::<Vec<String>>().oxford("and");
                    let word = if self.action.should_pluralize() {"times"} else {"time"};
                    write!(&mut output, "{} {} {}", courses, self.action.print()?, word)?;
                },
                (RepeatMode::All, What::Credits) => {
                    // TODO: special-case "once" and "twice"
                    let courses = courses.iter().map(|r| r.print().unwrap()).collect::<Vec<String>>().oxford("and");
                    let word = if self.action.should_pluralize() {"credits"} else {"credit"};
                    write!(&mut output, "{} enough times to yield {} {}", courses, self.action.print()?, word)?;
                },
                _ => unimplemented!(),
            }
            Given::TheseRequirements { requirements: _ } => {}
            Given::AreasOfStudy => {}
            Given::NamedVariable { save: _ } => {}
        }

        Ok(output)
    }
}

// impl Rule {
//     fn validate(&self) -> Result<(), util::ValidationError> {
//         match (&self.given, &self.what) {
//             (Given::AreasOfStudy, What::AreasOfStudy) => (),
//             (Given::AreasOfStudy, _) => {
//                 return Err(util::ValidationError::GivenAreasMustOutputAreas)
//             }
//             _ => (),
//         }
//
//         Ok(())
//     }
// }

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given")]
pub enum Given {
    #[serde(rename = "courses")]
    AllCourses,
    #[serde(rename = "these courses")]
    TheseCourses {
        courses: Vec<CourseRule>,
        repeats: RepeatMode,
    },
    #[serde(rename = "these requirements")]
    TheseRequirements {
        requirements: Vec<requirement::Rule>,
    },
    #[serde(rename = "areas of study")]
    AreasOfStudy,
    #[serde(rename = "save")]
    NamedVariable { save: String },
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum CourseRule {
    Value(#[serde(deserialize_with = "util::string_or_struct")] course::Rule),
}

impl crate::rules::traits::PrettyPrint for CourseRule {
    fn print(&self) -> Result<String, std::fmt::Error> {
        match &self {
            CourseRule::Value(v) => v.print()
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum RepeatMode {
    #[serde(rename = "first")]
    First,
    #[serde(rename = "last")]
    Last,
    #[serde(rename = "all")]
    All,
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
pub enum What {
    #[serde(rename = "courses")]
    Courses,
    #[serde(rename = "distinct courses")]
    DistinctCourses,
    #[serde(rename = "credits")]
    Credits,
    #[serde(rename = "departments")]
    Departments,
    #[serde(rename = "terms")]
    Terms,
    #[serde(rename = "grades")]
    Grades,
    #[serde(rename = "areas of study")]
    AreasOfStudy,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize_all_courses() {
        let data = Rule {
            given: Given::AllCourses,
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let expected = r#"---
given: courses
limit: []
where: {}
what: courses
do: count > 2"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_all_courses() {
        let data = r#"---
given: courses
limit: []
where: {}
what: courses
do: count > 2"#;

        let expected = Rule {
            given: Given::AllCourses,
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn serialize_these_courses() {
        let data = Rule {
            given: Given::TheseCourses {
                courses: vec![
                    CourseRule::Value(course::Rule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                    CourseRule::Value(course::Rule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                ],
                repeats: RepeatMode::First,
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let expected = r#"---
given: these courses
courses:
  - course: ASIAN 110
  - course: ASIAN 110
repeats: first
limit: []
where: {}
what: courses
do: count > 2"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_these_courses() {
        let data = r#"---
given: these courses
courses:
  - ASIAN 110
  - course: ASIAN 110
repeats: first
limit: []
where: {}
what: courses
do: count > 2"#;

        let expected = Rule {
            given: Given::TheseCourses {
                courses: vec![
                    CourseRule::Value(course::Rule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                    CourseRule::Value(course::Rule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                ],
                repeats: RepeatMode::First,
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn serialize_these_requirements() {
        let data = Rule {
            given: Given::TheseRequirements {
                requirements: vec![
                    requirement::Rule {
                        requirement: "A Name 1".to_string(),
                        optional: false,
                    },
                    requirement::Rule {
                        requirement: "A Name 2".to_string(),
                        optional: true,
                    },
                ],
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let expected = r#"---
given: these requirements
requirements:
  - requirement: A Name 1
    optional: false
  - requirement: A Name 2
    optional: true
limit: []
where: {}
what: courses
do: count > 2"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_these_requirements() {
        let data = r#"---
given: these requirements
requirements:
  - requirement: A Name 1
  - {requirement: A Name 2, optional: true}
limit: []
where: {}
what: courses
do: count > 2"#;

        let expected = Rule {
            given: Given::TheseRequirements {
                requirements: vec![
                    requirement::Rule {
                        requirement: "A Name 1".to_string(),
                        optional: false,
                    },
                    requirement::Rule {
                        requirement: "A Name 2".to_string(),
                        optional: true,
                    },
                ],
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn serialize_areas() {
        let data = Rule {
            given: Given::AreasOfStudy,
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::AreasOfStudy,
            action: "count > 2".parse().unwrap(),
        };

        let expected = r#"---
given: areas of study
limit: []
where: {}
what: areas of study
do: count > 2"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_areas() {
        let data = r#"---
given: areas of study
limit: []
where: {}
what: areas of study
do: count > 2"#;

        let expected = Rule {
            given: Given::AreasOfStudy,
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::AreasOfStudy,
            action: "count > 2".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn serialize_save() {
        let data = Rule {
            given: Given::NamedVariable {
                save: String::from("$my_var"),
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let expected = r#"---
given: save
save: $my_var
limit: []
where: {}
what: courses
do: count > 2"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_save() {
        let data = r#"---
given: save
save: $my_var
limit: []
where: {}
what: courses
do: count > 2"#;

        let expected = Rule {
            given: Given::NamedVariable {
                save: String::from("$my_var"),
            },
            limit: Some(vec![]),
            filter: Some(filter::Clause::new()),
            what: What::Courses,
            action: "count > 2".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_save_ba_interim() {
        let data = r#"---
given: save
save: $interim_courses
what: courses
do: count >= 3"#;

        let expected = Rule {
            given: Given::NamedVariable {
                save: String::from("$interim_courses"),
            },
            limit: None,
            filter: None,
            what: What::Courses,
            action: "count >= 3".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_filter_gereqs_single() {
        let data = r#"{where: {gereqs: 'FYW'}, given: courses, what: courses, do: count > 1}"#;

        let expected: filter::Clause = hashmap! {
            "gereqs".into() => filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::EqualTo,
                value: filter::Value::String("FYW".into()),
            }),
        };
        let expected = Rule {
            given: Given::AllCourses,
            limit: None,
            filter: Some(expected),
            what: What::Courses,
            action: "count > 1".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_filter_gereqs_or() {
        let data =
            r#"{where: {gereqs: 'MCD | MCG'}, given: courses, what: courses, do: count > 1}"#;

        let expected: filter::Clause = hashmap! {
            "gereqs".into() => filter::WrappedValue::Or([
                filter::TaggedValue {
                    op: action::Operator::EqualTo,
                    value: filter::Value::String("MCD".into()),
                },
                filter::TaggedValue {
                    op: action::Operator::EqualTo,
                    value: filter::Value::String("MCG".into()),
                },
            ]),
        };
        let expected = Rule {
            given: Given::AllCourses,
            limit: None,
            filter: Some(expected),
            what: What::Courses,
            action: "count > 1".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_filter_level_gte() {
        let data = r#"{where: {level: '>= 200'}, given: courses, what: courses, do: count > 1}"#;

        let expected: filter::Clause = hashmap! {
            "level".into() => filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::GreaterThanEqualTo,
                value: filter::Value::Integer(200),
            }),
        };
        let expected = Rule {
            given: Given::AllCourses,
            limit: None,
            filter: Some(expected),
            what: What::Courses,
            action: "count > 1".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_filter_graded_bool() {
        let data = r#"{where: {graded: 'true'}, given: courses, what: courses, do: count > 1}"#;

        let expected: filter::Clause = hashmap! {
            "graded".into() => filter::WrappedValue::Single(filter::TaggedValue {
                op: action::Operator::EqualTo,
                value: filter::Value::Bool(true),
            }),
        };
        let expected = Rule {
            given: Given::AllCourses,
            limit: None,
            filter: Some(expected),
            what: What::Courses,
            action: "count > 1".parse().unwrap(),
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn pretty_print_inline() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, what: courses, do: count >= 1}").unwrap();
        let expected = "at least one course";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_filters() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: courses, do: count >= 1}").unwrap();
        let expected = "at least one course with the “FOL-C” general education attribute";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {gereqs: SPM}, what: distinct courses, do: count >= 2}").unwrap();
        let expected = "at least two distinct courses with the “SPM” general education attribute";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_repeats() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 1}").unwrap();
        let expected = "THEAT 233 at least one time";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 4}").unwrap();
        let expected = "THEAT 233 at least four times";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: all, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 4}").unwrap();
        let expected = "THEAT 233 and THEAT 253 at least four times";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: all, courses: [THEAT 233], what: credits, do: sum >= 4}").unwrap();
        let expected = "THEAT 233 enough times to yield at least four credits";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: first, courses: [THEAT 233], what: courses, do: count >= 1}").unwrap();
        let expected = "THEAT 233";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: these courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 1}").unwrap();
        let expected = "THEAT 233 and THEAT 253";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_credits() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: credits, do: sum >= 1}").unwrap();
        let expected = "enough courses with the “FOL-C” general education attribute to obtain at least one credit";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {semester: Interim}, what: credits, do: sum >= 3}").unwrap();
        let expected = "enough courses during Interim semesters to obtain at least three credits";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {semester: Fall}, what: credits, do: sum >= 10}").unwrap();
        let expected = "enough courses during Fall semesters to obtain at least ten credits";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {semester: Fall | Interim}, what: credits, do: sum >= 10}").unwrap();
        let expected = "enough courses during a Fall or Interim semester to obtain at least ten credits";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {year: '2012'}, what: credits, do: sum >= 3}").unwrap();
        let expected = "enough courses during the 2012-13 academic year to obtain at least three credits";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {institution: St. Olaf College}, what: credits, do: sum >= 17}").unwrap();
        let expected = "enough courses at St. Olaf College to obtain at least 17 credits";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_departments() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: departments, do: count >= 2}").unwrap();
        let expected = "enough courses with the “FOL-C” general education attribute to span at least two departments";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: {semester: Interim}, what: departments, do: count >= 1}").unwrap();
        let expected = "enough courses during Interim semesters to span at least one department";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: { department: '! MATH' }, what: departments, do: count >= 2}").unwrap();
        let expected = "enough courses outside of the MATH department to span at least two departments";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_grades() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: { gereqs: FOL-C }, what: grades, do: average >= 2.0}").unwrap();
        let expected = "maintain an average GPA at or above 2.00 from courses with the “FOL-C” general education attribute";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: { semester: Interim }, what: grades, do: average >= 3.0}").unwrap();
        let expected = "maintain an average GPA at or above 3.00 from courses during Interim semesters";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_inline_terms() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: { gereqs: FOL-C }, what: terms, do: count >= 2}").unwrap();
        let expected = "enough courses with the “FOL-C” general education attribute to span at least two terms";
        assert_eq!(expected, input.print().unwrap());

        let input: Rule =
            serde_yaml::from_str(&"{given: courses, where: { semester: Interim }, what: terms, do: count >= 3}").unwrap();
        let expected = "enough courses during Interim semesters to span at least three terms";
        assert_eq!(expected, input.print().unwrap());
    }
}
