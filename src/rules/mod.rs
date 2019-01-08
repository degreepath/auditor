pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod requirement;

use crate::util::string_or_struct;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
    Course(#[serde(deserialize_with = "string_or_struct")] course::CourseRule),
    Requirement(requirement::RequirementRule),
    CountOf(count_of::CountOfRule),
    Both(both::BothRule),
    Either(either::EitherRule),
    Given(given::GivenRule),
}

mod tests {
    use super::*;

    #[test]
    fn serialize() {
        let course_a = course::CourseRule {
            course: "ASIAN 101".to_string(),
            section: None,
            term: None,
            semester: None,
            year: None,
            international: None,
            lab: None,
        };
        let course_b = course::CourseRule {
            course: "ASIAN 101".to_string(),
            section: None,
            term: Some("2014-1".to_string()),
            semester: None,
            year: None,
            international: None,
            lab: None,
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
            Rule::Given(given::GivenRule::AllCourses(given::GivenAllCoursesRule {
                given: "courses".to_string(),
                what: given::GivenWhatToGiveEnum::Courses,
                filter: vec![],
                limit: vec![],
                action: given::DoAction {
                    command: given::RuleAction::Count,
                    lhs: "a".to_string(),
                    operator: given::RuleOperator::LessThan,
                    rhs: "b".to_string(),
                },
            })),
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
  what: Courses
  where: []
  limit: []
  do:
    command: Count
    lhs: a
    operator: "<"
    rhs: b"#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize() {
        let data = r#"---
- ASIAN 101
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
    - ASIAN 101
- both:
    - ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- either:
    - ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
- given: courses
  what: Courses
  where: []
  limit: []
  do:
    command: Count
    lhs: a
    operator: "<"
    rhs: b"#;
        let course_a = course::CourseRule {
            course: "ASIAN 101".to_string(),
            section: None,
            term: None,
            semester: None,
            year: None,
            international: None,
            lab: None,
        };
        let course_b = course::CourseRule {
            course: "ASIAN 101".to_string(),
            section: None,
            term: Some("2014-1".to_string()),
            semester: None,
            year: None,
            international: None,
            lab: None,
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
            Rule::Given(given::GivenRule::AllCourses(given::GivenAllCoursesRule {
                given: "courses".to_string(),
                what: given::GivenWhatToGiveEnum::Courses,
                filter: vec![],
                limit: vec![],
                action: given::DoAction {
                    command: given::RuleAction::Count,
                    lhs: "a".to_string(),
                    operator: given::RuleOperator::LessThan,
                    rhs: "b".to_string(),
                },
            })),
        ];

        let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
