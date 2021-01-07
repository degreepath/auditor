use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AuditResult {}

impl ToProse for AuditResult {
    fn to_prose(
        &self,
        _f: &mut std::fmt::Formatter<'_>,
        _student: &Student,
        _options: &ProseOptions,
        _indent: usize,
    ) -> std::fmt::Result {
        todo!()
    }
}
