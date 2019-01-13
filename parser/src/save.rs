use crate::rules::given::{action, filter, limit, Given, What};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct SaveBlock {
    pub name: String,
    pub label: String,
    #[serde(flatten)]
    pub given: Given,
    #[serde(default)]
    pub limit: Option<Vec<limit::Limiter>>,
    #[serde(rename = "where", default, deserialize_with="filter::deserialize_with")]
    pub filter: Option<filter::Clause>,
    #[serde(default)]
    pub what: Option<What>,
    #[serde(rename = "do", default, deserialize_with = "action::option_action")]
    pub action: Option<action::Action>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rules::{course, given};

    #[test]
    fn deserialize() {
        let data = r#"---
given: courses
where: { semester: Interim }
what: courses
name: $interim_courses
label: Interim Courses"#;

        let filter: filter::Clause = hashmap! {
            "semester".into() => "Interim".parse::<filter::WrappedValue>().unwrap(),
        };

        let expected = SaveBlock {
            name: "$interim_courses".to_string(),
            label: "Interim Courses".to_string(),
            given: Given::AllCourses,
            limit: None,
            filter: Some(filter),
            what: Some(What::Courses),
            action: None,
        };

        let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_dance() {
        let data = r#"---
given: these courses
courses: [DANCE 399]
where: {year: graduation-year, semester: Fall}
name: $dance_seminars
label: "Senior Dance Seminars""#;

        let filter: filter::Clause = hashmap! {
            "year".into() => "graduation-year".parse::<filter::WrappedValue>().unwrap(),
            "semester".into() => "Fall".parse::<filter::WrappedValue>().unwrap(),
        };

        let expected = SaveBlock {
            name: "$dance_seminars".to_string(),
            label: "Senior Dance Seminars".to_string(),
            given: Given::TheseCourses {
                courses: vec![given::CourseRule::Value(course::Rule {
                    course: "DANCE 399".to_string(),
                    ..Default::default()
                })],
            },
            limit: None,
            filter: Some(filter),
            what: None,
            action: None,
        };

        let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

        assert_eq!(actual, expected);
    }
}
