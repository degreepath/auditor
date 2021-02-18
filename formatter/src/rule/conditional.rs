use crate::path::Path;
use crate::predicate_expression::StaticPredicateExpression;
use crate::rule::{Rule, RuleStatus};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use crate::to_record::{Record, RecordOptions, RecordStatus, ToRecord};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConditionalRule {
    pub condition: StaticPredicateExpression,
    pub max_rank: String,
    pub path: Path,
    pub rank: String,
    pub status: RuleStatus,
    pub when_false: Option<Box<Rule>>,
    pub when_true: Box<Rule>,
}

impl ToProse for ConditionalRule {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        if options.show_paths {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "path: {}", self.path)?;
        };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "If: [{}]", self.condition)?;

        let branch = self.condition.result();
        let true_branch = if branch == Some(true) { "t." } else { "" };
        let false_branch = if branch == Some(false) { "f!" } else { "" };

        writeln!(f, "Then ({})", true_branch)?;

        self.when_true.to_prose(f, student, options, indent + 1)?;

        writeln!(f)?;

        writeln!(f, "Else ({})", false_branch)?;

        if let Some(pred) = &self.when_false {
            pred.to_prose(f, student, options, indent + 1)?;
            writeln!(f)?;
        } else {
            write!(f, "do nothing")?;
        }

        Ok(())
    }
}

impl ToRecord for ConditionalRule {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        let is_waived = is_waived || self.status.is_waived();

        let conditional_string = format!("{}", self.condition);
        let if_true = self.when_true.get_row(student, options, is_waived);
        let if_false = if let Some(b) = &self.when_false {
            b.get_row(student, options, is_waived)
        } else {
            vec![]
        };

        let mut row = vec![];

        let header = format!("Conditional: {}", conditional_string);

        row.extend(if_true.into_iter().map(|sub_record| Record {
            title: header.clone(),
            subtitle: Some(format!("If yes: {}", sub_record.title)),
            status: *self.when_true.status(),
            content: sub_record.content,
        }));

        row.extend(if_false.into_iter().map(|sub_record| Record {
            title: header.clone(),
            subtitle: Some(format!("Otherwise: {}", sub_record.title)),
            status: if let Some(when_false) = self.when_false.clone() {
                *when_false.status()
            } else {
                RecordStatus::Empty
            },
            content: sub_record.content,
        }));

        row
    }

    fn get_requirements(&self) -> Vec<String> {
        let mut true_reqs = self.when_true.get_requirements();
        let false_reqs = match &self.when_false {
            Some(r) => r.get_requirements(),
            None => vec![],
        };

        true_reqs.extend(false_reqs.into_iter());

        true_reqs
    }
}
