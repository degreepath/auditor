use super::*;

impl super::Rule {
	pub fn to_rule(&self) -> crate::rules::Rule {
		crate::rules::Rule::Course(self.clone())
	}
}

impl super::Rule {
	pub fn check(
		&self,
		transcript: &[CourseInstance],
		already_used: &[(CourseInstance, super::Rule, MatchedCourseParts)],
	) -> RuleState<super::Rule> {
		RuleState::pass(self.to_rule())
	}
}

pub struct CourseInstance {
	course: String,
	department: String,
	section: String,
	term: String,
	year: u64,
	semester: String,
	gereqs: Vec<String>,
	attributes: Vec<String>,
	course_type: String,
}

pub struct MatchedCourseParts {
	course: MatchType<String>,
	section: MatchType<String>,
	term: MatchType<String>,
	year: MatchType<u64>,
	semester: MatchType<String>,
	course_type: MatchType<String>,
	gereqs: MatchType<Vec<MatchType<String>>>,
	attributes: MatchType<Vec<MatchType<String>>>,
}

impl MatchedCourseParts {
	pub fn any(&self) -> bool {
		self.course.matched()
			|| self.section.matched()
			|| self.term.matched()
			|| self.year.matched()
			|| self.semester.matched()
			|| self.course_type.matched()
			|| self.gereqs.matched()
			|| self.attributes.matched()
	}

	pub fn all(&self) -> bool {
		self.course.matched()
			&& self.section.matched()
			&& self.term.matched()
			&& self.year.matched()
			&& self.semester.matched()
			&& self.course_type.matched()
			&& self.gereqs.matched()
			&& self.attributes.matched()
	}
}

pub enum MatchType<T> {
	Match(T),
	Skip,
	Fail,
}

impl<T> MatchType<T> {
	pub fn matched(&self) -> bool {
		match &self {
			MatchType::Match(_) => true,
			_ => false,
		}
	}

	pub fn skipped(&self) -> bool {
		match &self {
			MatchType::Skip => true,
			_ => false,
		}
	}

	pub fn failed(&self) -> bool {
		match &self {
			MatchType::Fail => true,
			_ => false,
		}
	}
}

impl CourseInstance {
	pub fn matches_filter(&self, filter: &crate::rules::course::Rule) -> MatchedCourseParts {
		let course = match (&self.course, &filter.course) {
			(a, b) if a == b => MatchType::Match(a.clone()),
			_ => MatchType::Fail,
		};

		let section = match (&self.section, &filter.section) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let term = match (&self.term, &filter.term) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let year = match (&self.year, &filter.year) {
			(a, Some(b)) if a == b => MatchType::Match(*a),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let semester = match (&self.semester, &filter.semester) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let course_type = match (&self.course_type, &filter.lab) {
			(a, Some(b)) if *b == true && a == "Lab" => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		MatchedCourseParts {
			course,
			section,
			term,
			year,
			semester,
			course_type,
			attributes: MatchType::Skip,
			gereqs: MatchType::Skip,
		}
	}
}

pub struct AuditState {
	courses: Vec<CourseInstance>,
}

impl AuditState {
	pub fn has_course_matching(&self, filter: &crate::rules::course::Rule) -> bool {
		self.courses.iter().any(|c| c.matches_filter(filter).any())
	}
}

enum Status {
	Pass,
	Fail,
	Skipped,
	Pending,
}

pub struct RuleState {
	rule: crate::rules::Rule,
	matched_courses: Vec<CourseInstance>,
	status: Status,
}

impl RuleState {
	pub fn pass(rule: crate::rules::Rule) -> RuleState {
		RuleState {
			rule: rule.clone(),
			matched_courses: vec![],
			status: Status::Pass,
		}
	}

	pub fn fail(rule: crate::rules::Rule) -> RuleState {
		RuleState {
			rule: rule.clone(),
			matched_courses: vec![],
			status: Status::Fail,
		}
	}

	pub fn is_pass(&self) -> bool {
		match self.status {
			Status::Pass => true,
			_ => false,
		}
	}

	pub fn is_fail(&self) -> bool {
		match self.status {
			Status::Fail => true,
			_ => false,
		}
	}
}
