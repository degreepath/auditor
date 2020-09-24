use crate::operator::Operator;
use crate::predicate_expression::{PredicateExpression, StaticPredicateConditionFunction};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum CompoundPredicate {
    #[serde(rename = "pred--or")]
    Or { predicates: Vec<CompoundPredicate> },
    #[serde(rename = "pred--and")]
    And { predicates: Vec<CompoundPredicate> },
    #[serde(rename = "pred--if")]
    Conditional(ConditionalPredicate),
    #[serde(rename = "predicate")]
    Predicate(Predicate),
}

impl ToProse for CompoundPredicate {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        match self {
            CompoundPredicate::Or { predicates } => {
                self.join_predicates(f, predicates, student, options, indent, "or ")
            }
            CompoundPredicate::And { predicates } => {
                self.join_predicates(f, predicates, student, options, indent, "and ")
            }
            CompoundPredicate::Conditional(p) => p.to_prose(f, student, options, indent),
            CompoundPredicate::Predicate(p) => p.to_prose(f, student, options, indent),
        }
    }
}

impl CompoundPredicate {
    fn join_predicates(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        predicates: &[CompoundPredicate],
        student: &Student,
        options: &ProseOptions,
        indent: usize,
        joiner: &str,
    ) -> std::fmt::Result {
        let indent_str = " ".repeat(indent * 4);

        for (i, p) in predicates.iter().enumerate() {
            p.to_prose(f, student, options, indent)?;

            if i != predicates.len() - 1 {
                writeln!(f)?;
                f.write_str(indent_str.as_str())?;
                f.write_str(joiner)?;
            }
        }

        Ok(())
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Predicate {
    pub expected: serde_json::Value,
    pub expected_verbatim: Option<serde_json::Value>,
    pub key: String,
    pub operator: Operator,
    pub label: Option<String>,
}

impl ToProse for Predicate {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        _student: &Student,
        _options: &ProseOptions,
        _indent: usize,
    ) -> std::fmt::Result {
        let key = match self.key.as_str() {
            "attributes" => "bucket",
            "is_in_progress" => "in-progress",
            "is_stolaf" => "from STOLAF",
            _ => self.key.as_str(),
        };

        let expected = self.expected.clone();

        let op = format!("{}", self.operator);

        if self.operator == Operator::EqualTo && expected == serde_json::Value::Bool(true) {
            write!(f, "{}", key)?;
        } else if self.operator == Operator::EqualTo && expected == serde_json::Value::Bool(false) {
            write!(f, "not {}", key)?;
        } else {
            write!(f, "{} {} {}", key, op, expected)?;
        }

        if let Some(v) = &self.expected_verbatim {
            write!(f, " [via {:?}]", v)?;
        }

        if let Some(label) = &self.label {
            write!(f, " [label: {:?}]", label)?;
        }

        Ok(())
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConditionalPredicate {
    pub condition: PredicateExpression<StaticPredicateConditionFunction>,
    pub when_true: Box<CompoundPredicate>,
    pub when_false: Option<Box<CompoundPredicate>>,
}

impl ToProse for ConditionalPredicate {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        write!(f, "If: [{}] ", self.condition)?;

        let branch = self.condition.result;
        let true_branch = if branch == Some(true) { "t." } else { "" };
        let false_branch = if branch == Some(false) { "f!" } else { "" };

        write!(f, "Then ({}): [", true_branch)?;
        self.when_true.to_prose(f, student, options, indent)?;
        write!(f, "] ")?;

        write!(f, "Else ({}): [", false_branch)?;
        if let Some(pred) = &self.when_false {
            pred.to_prose(f, student, options, indent)?;
        } else {
            f.write_str("do nothing")?;
        }
        write!(f, "]")?;

        Ok(())
    }
}
