use crate::path::Path;
use crate::student::{ClassLabId, CourseId};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Claim {
    pub claimed_by: Path,
    pub clbid: ClassLabId,
    pub crsid: CourseId,
}
