use crate::area_of_study::AreaOfStudy;
use crate::student::Student;

pub trait ToHtml {
    fn to_html(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &HtmlOptions,
        indent: usize,
    ) -> std::fmt::Result;
}

pub struct HtmlOptions {
    pub show_paths: bool,
    pub show_ranks: bool,
}

pub struct HtmlContext<'a, 'b, 'c> {
    pub result: &'c AreaOfStudy,
    pub student: &'a Student,
    pub options: &'b HtmlOptions,
}

impl<'a, 'b, 'c> std::fmt::Display for HtmlContext<'a, 'b, 'c> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.result.to_html(f, self.student, self.options, 0)
    }
}
