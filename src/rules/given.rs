use crate::rules::requirement::RequirementRule;
use std::str::FromStr;

use super::course::CourseRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum GivenRule {
    AllCourses(GivenAllCoursesRule),
    TheseCourses(GivenTheseCoursesRule),
    TheseRequirements(GivenTheseRequirementsRule),
    AreasOfStudy(GivenAreasOfStudyRule),
    NamedVariable(GivenNamedVariableRule),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenAllCoursesRule {
    pub given: String,
    pub what: GivenWhatToGiveEnum,
    #[serde(default, rename = "where")]
    pub filter: Vec<GivenWhereClause>,
    #[serde(default)]
    pub limit: Vec<GivenLimiter>,
    #[serde(rename = "do")]
    pub action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct DoAction {
    pub command: RuleAction,
    pub lhs: String,
    pub operator: RuleOperator,
    pub rhs: String,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenTheseCoursesRule {
    pub given: String,
    pub courses: Vec<CourseRule>,
    #[serde(rename = "where")]
    pub filter: Vec<GivenWhereClause>,
    pub limit: Vec<GivenLimiter>,
    pub what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    pub action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenTheseRequirementsRule {
    pub given: String,
    pub requirements: Vec<RequirementRule>,
    #[serde(rename = "where")]
    pub filter: Vec<GivenWhereClause>,
    pub limit: Vec<GivenLimiter>,
    pub what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    pub action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenNamedVariableRule {
    pub given: String,
    #[serde(rename = "where")]
    pub filter: Vec<GivenWhereClause>,
    pub limit: Vec<GivenLimiter>,
    pub what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    pub action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenWhereClause {
    pub key: String,
    pub value: String,
    pub operation: GivenWhereOp,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum GivenWhereOp {
    Eq,
    NotEq,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenLimiter {}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct GivenAreasOfStudyRule {
    pub given: String,
    #[serde(rename = "where")]
    pub filter: Vec<GivenWhereClause>,
    pub limit: Vec<GivenLimiter>,
    pub what: GivenWhatToGiveAreasEnum,
    #[serde(rename = "do")]
    pub action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum GivenWhatToGiveEnum {
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

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum GivenWhatToGiveAreasEnum {
    #[serde(rename = "areas of study")]
    AreasOfStudy,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum RuleAction {
    Count,
    Sum,
    Average,
    Minimum,
    Difference,
    NamedVariable(String),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum RuleOperator {
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
