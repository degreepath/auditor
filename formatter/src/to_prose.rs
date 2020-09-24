use crate::area_of_study::AreaOfStudy;
use crate::student::Student;

pub trait ToProse {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result;
}

pub struct ProseOptions {
    pub show_paths: bool,
    pub show_ranks: bool,
}

pub struct ProseContext<'a, 'b, 'c> {
    pub result: &'c AreaOfStudy,
    pub student: &'a Student,
    pub options: &'b ProseOptions,
}

impl<'a, 'b, 'c> std::fmt::Display for ProseContext<'a, 'b, 'c> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.result.to_prose(f, self.student, self.options, 0)
    }
}
