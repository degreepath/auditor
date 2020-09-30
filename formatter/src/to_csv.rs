use crate::student::Student;

pub trait ToCsv {
    fn get_record(
        &self,
        student: &Student,
        options: &CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)>;
}

pub struct CsvOptions {}
