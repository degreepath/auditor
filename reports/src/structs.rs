use formatter::{student::StudentClassification, to_record::Record};

pub struct MappedResult {
    pub(crate) cells: Vec<Record>,
    pub(crate) catalog: String,
    pub(crate) stnum: String,
    pub(crate) requirements: Vec<String>,
    pub(crate) emphases: Vec<String>,
    pub(crate) emphasis_req_names: Vec<String>,
    pub(crate) student_name: String,
    pub(crate) classification: StudentClassification,
}
