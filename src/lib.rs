#[macro_use]
extern crate serde_derive;

extern crate serde_yaml;
use std::str::FromStr;

fn serde_false() -> bool {
    false
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Point {
    x: f64,
    y: f64,
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }


    extern crate serde_yaml;

    use crate::Point;

    #[test]
    fn serde() {
        let point = Point { x: 1.0, y: 2.0 };

        let s = serde_yaml::to_string(&point).unwrap();
        assert_eq!(s, "---\nx: 1.0\ny: 2.0");

        let deserialized_point: Point = serde_yaml::from_str(&s).unwrap();
        assert_eq!(point, deserialized_point);
    }

    use crate::CountOfEnum;

    #[test]
    fn count_of_parse() {
        let count = CountOfEnum::Any;

        let s = serde_yaml::to_string(&count).unwrap();
        assert_eq!(s, "---\nany");

        let s = "---\nany";
        let deserialized_count: CountOfEnum = serde_yaml::from_str(&s).unwrap();
        assert_eq!(deserialized_count, count);
    }
}


#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct AreaOfStudy {
    #[serde(rename = "name")]
    area_name: String,
    #[serde(rename = "type")]
    area_type: String,
    catalog: String,

    result: Rule,
    requirements: Vec<Section>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
enum Rule {
    Course(CourseRule),
    Requirement(RequirementRule),
    CountOf(CountOfRule),
    Both(BothRule),
    Either(EitherRule),
    Given(GivenRule),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct CourseRule {
    department: String,
    number: u16,
    term: Option<String>,
    section: Option<String>,
    year: Option<u16>,
    semester: Option<String>,
    lab: Option<bool>,
    international: Option<bool>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct RequirementRule {
    requirement: String,
    #[serde(default = "serde_false")]
    optional: bool,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum CountOfEnum {
    // TODO: get "all" and "any" to parse into the enum properly
    #[serde(rename = "all")]
    All,
    #[serde(rename = "any")]
    Any,
    Number { value: u8 },
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct CountOfRule {
    count: CountOfEnum,
    of: Vec<Rule>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct BothRule {
    both: (Box<Rule>, Box<Rule>),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct EitherRule {
    either: (Box<Rule>, Box<Rule>),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
enum GivenRule {
    AllCourses(GivenAllCoursesRule),
    TheseCourses(GivenTheseCoursesRule),
    TheseRequirements(GivenTheseRequirementsRule),
    AreasOfStudy(GivenAreasOfStudyRule),
    NamedVariable(GivenNamedVariableRule),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenAllCoursesRule {
    given: String,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct DoAction {
    command: RuleAction,
    lhs: String,
    operator: RuleOperator,
    rhs: String,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenTheseCoursesRule {
    given: String,
    courses: Vec<CourseRule>,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenTheseRequirementsRule {
    given: String,
    requirements: Vec<RequirementRule>,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenNamedVariableRule {
    given: String,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenWhereClause {
    key: String,
    value: String,
    operation: GivenWhereOp,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum GivenWhereOp {
    Eq,
    NotEq,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenLimiter {}


#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct GivenAreasOfStudyRule {
    given: String,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveAreasEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum GivenWhatToGiveEnum {
    Courses,
    DistinctCourses,
    Credits,
    Terms,
    Grades,
}

impl FromStr for GivenWhatToGiveEnum {
    type Err = ();

    fn from_str(s: &str) -> Result<GivenWhatToGiveEnum, ()> {
        match s {
            "courses" => Ok(GivenWhatToGiveEnum::Courses),
            "distinct courses" => Ok(GivenWhatToGiveEnum::DistinctCourses),
            "credits" => Ok(GivenWhatToGiveEnum::Credits),
            "terms" => Ok(GivenWhatToGiveEnum::Terms),
            "Grades" => Ok(GivenWhatToGiveEnum::Grades),
            _ => Err(()),
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum GivenWhatToGiveAreasEnum {
    #[serde(rename = "areas of study")]
    AreasOfStudy,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum RuleOperator {
    #[serde(rename = "<")]
    LessThan,
    #[serde(rename = "<=")]
    LessThanOrEqualTo,
    #[serde(rename = "=")]
    EqualTo,
    #[serde(rename = ">")]
    GreaterThan,
    #[serde(rename = ">=")]
    GreaterThanOrEqualTo,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
enum RuleAction {
    Count,
    Sum,
    Average,
    Minimum,
    Difference,
    NamedVariable(String),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Requirement {
    message: Option<String>,
    #[serde(default = "serde_false")]
    department_audited: bool,
    result: Rule,
    #[serde(default = "serde_false")]
    contract: bool,
    save: Vec<SaveBlock>,
}

// should be a superset of GivenRule...
#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct SaveBlock {
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
enum Section {
    Subsection(Subsection),
    Requirement(Requirement),
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Subsection {
    message: Option<String>,
}
