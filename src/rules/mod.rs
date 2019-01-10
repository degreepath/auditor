pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod requirement;

use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
    Course(#[serde(deserialize_with = "util::string_or_struct")] course::CourseRule),
    Requirement(requirement::RequirementRule),
    CountOf(count_of::CountOfRule),
    Both(both::BothRule),
    Either(either::EitherRule),
    Given(given::Rule),
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn deserialize_simple_course_in_array() {
        let data = "---
- STAT 214";

        let expected_struct = vec![Rule::Course(course::CourseRule {
            course: "STAT 214".to_owned(),
            ..Default::default()
        })];

        let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }

    #[test]
    fn serialize() {
        let course_a = course::CourseRule {
            course: "ASIAN 101".to_string(),
            ..Default::default()
        };
        let course_b = course::CourseRule {
            course: "ASIAN 101".to_string(),
            term: Some("2014-1".to_string()),
            ..Default::default()
        };
        let data = vec![
            Rule::Course(course_a.clone()),
            Rule::Course(course_b.clone()),
            Rule::Requirement(requirement::RequirementRule {
                requirement: "Name".to_string(),
                optional: true,
            }),
            Rule::CountOf(count_of::CountOfRule {
                count: count_of::CountOfEnum::Number(1),
                of: vec![Rule::Course(course_a.clone())],
            }),
            Rule::Both(both::BothRule {
                both: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Either(either::EitherRule {
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
  do:
    lhs:
      Command: Count
    op: LessThan
    rhs:
      Integer: 2"#;

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
  do:
    lhs:
      Command: Count
    op: LessThan
    rhs:
      Integer: 2"#;

        let course_a = course::CourseRule {
            course: "ASIAN 101".to_string(),
            ..Default::default()
        };
        let course_b = course::CourseRule {
            course: "ASIAN 101".to_string(),
            term: Some("2014-1".to_string()),
            ..Default::default()
        };
        let expected = vec![
            Rule::Course(course_a.clone()),
            Rule::Course(course_b.clone()),
            Rule::Requirement(requirement::RequirementRule {
                requirement: "Name".to_string(),
                optional: true,
            }),
            Rule::CountOf(count_of::CountOfRule {
                count: count_of::CountOfEnum::Number(1),
                of: vec![Rule::Course(course_a.clone())],
            }),
            Rule::Both(both::BothRule {
                both: (
                    Box::new(Rule::Course(course_a.clone())),
                    Box::new(Rule::Course(course_b.clone())),
                ),
            }),
            Rule::Either(either::EitherRule {
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
        ];

        let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
