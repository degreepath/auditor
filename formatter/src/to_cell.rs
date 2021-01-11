use crate::student::Student;

pub trait ToCell {
    fn get_record(
        &self,
        student: &Student,
        options: &CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)>;

    fn get_requirements(&self) -> Vec<String>;
}

pub struct CsvOptions {}
