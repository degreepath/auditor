use crate::student::Student;

pub trait ToCsv {
    fn get_record(&self, student: &Student, options: &CsvOptions) -> Vec<(String, String)>;
}

pub struct CsvOptions {}
