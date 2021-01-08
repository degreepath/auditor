use formatter::student::StudentClassification;

pub(crate) struct MappedResult {
    pub(crate) header: Vec<String>,
    pub(crate) data: Vec<String>,
    pub(crate) catalog: String,
    pub(crate) stnum: String,
    pub(crate) requirements: Vec<String>,
    pub(crate) emphases: Vec<String>,
    pub(crate) emphasis_req_names: Vec<String>,
    pub(crate) name: String,
    pub(crate) classification: StudentClassification,
}
