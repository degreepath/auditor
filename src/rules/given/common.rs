use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum WhatToGive {
    Courses,
    DistinctCourses,
    Credits,
    Terms,
    Grades,
    AreasOfStudy,
}

impl FromStr for WhatToGive {
    type Err = ();

    fn from_str(s: &str) -> Result<WhatToGive, ()> {
        match s {
            "courses" => Ok(WhatToGive::Courses),
            "distinct courses" => Ok(WhatToGive::DistinctCourses),
            "credits" => Ok(WhatToGive::Credits),
            "terms" => Ok(WhatToGive::Terms),
            "grades" => Ok(WhatToGive::Grades),
            "areas of study" => Ok(WhatToGive::AreasOfStudy),
            _ => Err(()),
        }
    }
}
