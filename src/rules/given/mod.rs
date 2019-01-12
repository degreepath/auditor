use crate::rules::{course, requirement};
use crate::util;

pub mod action;
pub mod filter;
pub mod limit;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(flatten)]
    pub given: Given,
    #[serde(default)]
    pub limit: Option<Vec<limit::Limiter>>,
    #[serde(default, rename = "where")]
    pub filter: Option<filter::Clause>,
    pub what: What,
    #[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
    pub action: action::Action,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given")]
pub enum Given {
    #[serde(rename = "courses")]
    AllCourses,
    #[serde(rename = "these courses")]
    TheseCourses { courses: Vec<CourseRule> },
    #[serde(rename = "these requirements")]
    TheseRequirements {
        requirements: Vec<requirement::RequirementRule>,
    },
    #[serde(rename = "areas of study")]
    AreasOfStudy,
    // #[serde(rename = "save", deserialize_with = "util::string_or_struct")]
    #[serde(rename = "save")]
    NamedVariable { save: String },
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum CourseRule {
    Value(#[serde(deserialize_with = "util::string_or_struct")] course::CourseRule),
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
                    CourseRule::Value(course::CourseRule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                    CourseRule::Value(course::CourseRule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                ],
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
limit: []
where: {}
what: courses
do: count > 2"#;

        let expected = Rule {
            given: Given::TheseCourses {
                courses: vec![
                    CourseRule::Value(course::CourseRule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
                    CourseRule::Value(course::CourseRule {
                        course: "ASIAN 110".to_string(),
                        ..Default::default()
                    }),
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
    fn serialize_these_requirements() {
        let data = Rule {
            given: Given::TheseRequirements {
                requirements: vec![
                    requirement::RequirementRule {
                        requirement: "A Name 1".to_string(),
                        optional: false,
                    },
                    requirement::RequirementRule {
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
                    requirement::RequirementRule {
                        requirement: "A Name 1".to_string(),
                        optional: false,
                    },
                    requirement::RequirementRule {
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
}
