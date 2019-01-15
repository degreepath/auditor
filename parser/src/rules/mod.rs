pub mod action;
pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod requirement;
pub mod traits;

use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
    Course(#[serde(deserialize_with = "util::string_or_struct")] course::Rule),
    Requirement(requirement::Rule),
    CountOf(count_of::Rule),
    Both(both::Rule),
    Either(either::Rule),
    Given(given::Rule),
    Do(action::Rule),
}

impl crate::rules::traits::PrettyPrint for Rule {
    fn print(&self) -> Result<String, std::fmt::Error> {
        match &self {
            Rule::Course(v) => v.print(),
            Rule::Requirement(v) => v.print(),
            Rule::CountOf(v) => v.print(),
            Rule::Both(v) => v.print(),
            Rule::Either(v) => v.print(),
            Rule::Given(v) => v.print(),
            Rule::Do(v) => v.print(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn deserialize_simple_course_in_array() {
        let data = "---
- STAT 214";

        let expected_struct = vec![Rule::Course(course::Rule {
            course: "STAT 214".to_string(),
            ..Default::default()
        })];

        let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }

    #[test]
    fn serialize() {
        let course_a = course::Rule {
            course: "ASIAN 101".to_string(),
            ..Default::default()
        };
        let course_b = course::Rule {
            course: "ASIAN 101".to_string(),
            term: Some("2014-1".to_string()),
            ..Default::default()
        };
        let data = vec![
            Rule::Course(course_a.clone()),
            Rule::Course(course_b.clone()),
            Rule::Requirement(requirement::Rule {
                requirement: "Name".to_string(),
                optional: true,
            }),
            Rule::CountOf(count_of::Rule {
                count: count_of::Counter::Number(1),
                of: vec![Rule::Course(course_a.clone())],
            }),
            Rule::Both(both::Rule {
                both: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Either(either::Rule {
                either: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Given(given::Rule {
                given: given::Given::AllCourses,
                what: given::What::Courses,
                filter: Some(HashMap::new()),
                limit: Some(vec![]),
                action: "count < 2".parse().unwrap(),
            }),
            Rule::Do(action::Rule {
                action: "$a < $b".parse().unwrap(),
            }),
        ];

        let expected = r#"---
- course: ASIAN 101
- course: ASIAN 101
  term: 2014-1
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- given: courses
  limit: []
  where: {}
  what: courses
  do: count < 2
- do: $a < $b"#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize() {
        let data = r#"---
- course: ASIAN 101
- course: ASIAN 101
  term: 2014-1
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- given: courses
  what: courses
  where: {}
  limit: []
  do: count < 2
- do: $a < $b"#;

        let course_a = course::Rule {
            course: "ASIAN 101".to_string(),
            ..Default::default()
        };
        let course_b = course::Rule {
            course: "ASIAN 101".to_string(),
            term: Some("2014-1".to_string()),
            ..Default::default()
        };
        let expected = vec![
            Rule::Course(course_a.clone()),
            Rule::Course(course_b.clone()),
            Rule::Requirement(requirement::Rule {
                requirement: "Name".to_string(),
                optional: true,
            }),
            Rule::CountOf(count_of::Rule {
                count: count_of::Counter::Number(1),
                of: vec![Rule::Course(course_a.clone())],
            }),
            Rule::Both(both::Rule {
                both: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Either(either::Rule {
                either: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Given(given::Rule {
                given: given::Given::AllCourses,
                what: given::What::Courses,
                filter: Some(HashMap::new()),
                limit: Some(vec![]),
                action: "count < 2".parse().unwrap(),
            }),
            Rule::Do(action::Rule {
                action: "$a < $b".parse().unwrap(),
            }),
        ];

        let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_shorthands() {
        let data = r#"---
- ASIAN 101
- course: ASIAN 101
- {course: ASIAN 102, term: 2014-1}
- requirement: Name 1
- {requirement: Name 2, optional: true}
- count: 1
  of:
    - ASIAN 101
- both:
    - ASIAN 101
    - {course: ASIAN 102, term: 2014-1}
- either:
    - ASIAN 101
    - {course: ASIAN 102, term: 2014-1}
- given: courses
  what: courses
  do: count < 2
- do: $a < $b"#;

        let course_a = course::Rule {
            course: "ASIAN 101".to_string(),
            ..Default::default()
        };
        let course_b = course::Rule {
            course: "ASIAN 102".to_string(),
            term: Some("2014-1".to_string()),
            ..Default::default()
        };
        let expected = vec![
            Rule::Course(course_a.clone()),
            Rule::Course(course_a.clone()),
            Rule::Course(course_b.clone()),
            Rule::Requirement(requirement::Rule {
                requirement: "Name 1".to_string(),
                optional: false,
            }),
            Rule::Requirement(requirement::Rule {
                requirement: "Name 2".to_string(),
                optional: true,
            }),
            Rule::CountOf(count_of::Rule {
                count: count_of::Counter::Number(1),
                of: vec![Rule::Course(course_a.clone())],
            }),
            Rule::Both(both::Rule {
                both: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Either(either::Rule {
                either: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Given(given::Rule {
                given: given::Given::AllCourses,
                what: given::What::Courses,
                filter: None,
                limit: None,
                action: "count < 2".parse().unwrap(),
            }),
            Rule::Do(action::Rule {
                action: "$a < $b".parse().unwrap(),
            }),
        ];

        let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
