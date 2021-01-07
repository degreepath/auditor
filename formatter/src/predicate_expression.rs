use serde::{Deserialize, Serialize};
use std::fmt::Display;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PredicateExpressionCompoundAnd<T> {
    expressions: Vec<T>,
    result: Option<bool>,
}

impl<T> Display for PredicateExpressionCompoundAnd<T>
where
    T: Display,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        for (i, e) in self.expressions.iter().enumerate() {
            write!(f, "{}", e)?;
            if i != self.expressions.len() - 1 {
                f.write_str(" and ")?;
            }
        }

        Ok(())
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PredicateExpressionCompoundOr<T> {
    expressions: Vec<T>,
    result: Option<bool>,
}

impl<T> Display for PredicateExpressionCompoundOr<T>
where
    T: Display,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        for (i, e) in self.expressions.iter().enumerate() {
            write!(f, "{}", e)?;
            if i != self.expressions.len() - 1 {
                f.write_str(" or ")?;
            }
        }

        Ok(())
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PredicateExpressionNot<T> {
    expression: Box<T>,
    result: Option<bool>,
}

impl<T> Display for PredicateExpressionNot<T>
where
    T: Display,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let headline = match self.result {
            None => "??",
            Some(true) => "t.",
            Some(false) => "f!",
        };

        write!(f, "(NOT {} => {})", self.expression, headline)
    }
}

pub trait PredicateConditionFunction: Display + std::fmt::Debug {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PredicateExpression<Func>
where
    Func: PredicateConditionFunction,
{
    // not really optional... but something in 590's spec crashes here otherwise
    pub function: Option<Func>,
    pub argument: Option<String>,
    pub result: Option<bool>,
}

impl<Func> std::fmt::Display for PredicateExpression<Func>
where
    Func: PredicateConditionFunction,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let headline = match self.result {
            None => "??",
            Some(true) => "t.",
            Some(false) => "f!",
        };

        write!(
            f,
            "({:?} \"{:?}\" => {})",
            self.function, self.argument, headline
        )
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum StaticPredicateExpression {
    #[serde(rename = "pred-expr--and")]
    And(PredicateExpressionCompoundAnd<StaticPredicateExpression>),
    #[serde(rename = "pred-expr--or")]
    Or(PredicateExpressionCompoundOr<StaticPredicateExpression>),
    #[serde(rename = "pred-expr--not")]
    Not(PredicateExpressionNot<StaticPredicateExpression>),
    #[serde(rename = "pred-expr")]
    Expression(PredicateExpression<StaticPredicateConditionFunction>),
}

impl StaticPredicateExpression {
    pub fn result(&self) -> Option<bool> {
        match self {
            StaticPredicateExpression::And(e) => e.result,
            StaticPredicateExpression::Or(e) => e.result,
            StaticPredicateExpression::Not(e) => e.result,
            StaticPredicateExpression::Expression(e) => e.result,
        }
    }
}

impl Display for StaticPredicateExpression {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StaticPredicateExpression::And(e) => e.fmt(f),
            StaticPredicateExpression::Or(e) => e.fmt(f),
            StaticPredicateExpression::Not(e) => e.fmt(f),
            StaticPredicateExpression::Expression(e) => e.fmt(f),
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum DynamicPredicateExpression {
    #[serde(rename = "pred-dyn-expr--and")]
    And(PredicateExpressionCompoundAnd<DynamicPredicateExpression>),
    #[serde(rename = "pred-dyn-expr--or")]
    Or(PredicateExpressionCompoundOr<DynamicPredicateExpression>),
    #[serde(rename = "pred-dyn-expr--not")]
    Not(PredicateExpressionNot<DynamicPredicateExpression>),
    #[serde(rename = "pred-dyn-expr")]
    Expression(PredicateExpression<DynamicPredicateConditionFunction>),
}

impl DynamicPredicateExpression {
    pub fn result(&self) -> Option<bool> {
        match self {
            DynamicPredicateExpression::And(e) => e.result,
            DynamicPredicateExpression::Or(e) => e.result,
            DynamicPredicateExpression::Not(e) => e.result,
            DynamicPredicateExpression::Expression(e) => e.result,
        }
    }
}

impl Display for DynamicPredicateExpression {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DynamicPredicateExpression::And(e) => e.fmt(f),
            DynamicPredicateExpression::Or(e) => e.fmt(f),
            DynamicPredicateExpression::Not(e) => e.fmt(f),
            DynamicPredicateExpression::Expression(e) => e.fmt(f),
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum StaticPredicateConditionFunction {
    #[serde(rename = "has-ip-course")]
    HasIpCourse,
    #[serde(rename = "has-completed-course")]
    HasCompletedCourse,
    #[serde(rename = "has-course")]
    HasCourse,
    #[serde(rename = "passed-proficiency-exam")]
    PassedProficiencyExam,
    #[serde(rename = "has-declared-area-code")]
    HasDeclaredAreaCode,
    #[serde(rename = "student-has-course-with-attribute")]
    StudentHasCourseWithAttribute,
}

impl Display for StaticPredicateConditionFunction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        use StaticPredicateConditionFunction as F;
        let output = match self {
            F::HasIpCourse => "has-ip-course",
            F::HasCompletedCourse => "has-completed-course",
            F::HasCourse => "has-course",
            F::PassedProficiencyExam => "passed-proficiency-exam",
            F::HasDeclaredAreaCode => "has-declared-area-code",
            F::StudentHasCourseWithAttribute => "student-has-course-with-attribute",
        };
        f.write_str(output)
    }
}

impl PredicateConditionFunction for StaticPredicateConditionFunction {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum DynamicPredicateConditionFunction {
    #[serde(rename = "query-has-course-with-attribute")]
    QueryHasCourseWithAttribute,
    #[serde(rename = "query-has-single-course-with-attribute")]
    QueryHasSingleCourseWithAttribute,
}

impl Display for DynamicPredicateConditionFunction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        use DynamicPredicateConditionFunction as F;
        let output = match self {
            F::QueryHasCourseWithAttribute => "has-ip-course",
            F::QueryHasSingleCourseWithAttribute => "has-completed-course",
        };
        f.write_str(output)
    }
}

impl PredicateConditionFunction for DynamicPredicateConditionFunction {}
