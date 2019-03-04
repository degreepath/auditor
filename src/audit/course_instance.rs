use super::course_match::{MatchType, MatchedParts};
use crate::filter::CourseClause;
use crate::rules::course::Rule as CourseRule;
use crate::student::{CourseInstance, CourseType, GradeOption};

impl CourseInstance {
	pub fn matches_rule(&self, rule: &CourseRule) -> MatchedParts {
		let mut result = MatchedParts::default();

		if self.course == rule.course {
			result = MatchedParts {
				course: MatchType::Match(self.course.clone()),
				..result
			};
		}

		match (&self.section, &rule.section) {
			(Some(s_section), Some(r_section)) if s_section == r_section => {
				result = MatchedParts {
					section: MatchType::Match(s_section.clone()),
					..result
				};
			}
			_ => {}
		};

		if let Some(r_year) = &rule.year {
			if self.term.year == *r_year {
				result = MatchedParts {
					year: MatchType::Match(self.term.year.clone()),
					..result
				};
			}
		}

		if let Some(r_semester) = &rule.semester {
			if self.term.semester == *r_semester {
				result = MatchedParts {
					semester: MatchType::Match(self.term.semester.clone()),
					..result
				};
			}
		}

		if let Some(r_lab) = &rule.lab {
			if *r_lab && self.r#type == CourseType::Lab {
				result = MatchedParts {
					r#type: MatchType::Match(CourseType::Lab),
					..result
				};
			}
		}

		if let Some(r_grade) = &rule.grade {
			match &self.grade {
				GradeOption::Graded { grade: Some(s_grade) } => {
					if *s_grade >= *r_grade {
						result = MatchedParts {
							grade: MatchType::Match(s_grade.clone()),
							..result
						};
					}
				}
				_ => {}
			}
		}

		result
	}

	#[allow(dead_code)]
	pub fn matches_filter(&self, filter: &CourseClause) -> MatchedParts {
		let mut result = MatchedParts::default();

		if let Some(f_course) = &filter.course {
			if &self.course == f_course {
				result = MatchedParts {
					course: MatchType::Match(self.course.clone()),
					..result
				};
			}
		}

		result
	}
}
