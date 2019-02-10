use super::{CourseInstance, ReservedPairings};

#[derive(Debug, Clone, PartialEq)]
pub struct RuleResult {
	pub detail: RuleResultDetails,
	pub reservations: ReservedPairings,
	pub status: RuleStatus,
}

#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq)]
pub enum RuleResultDetails {
	Course,
	Requirement(RequirementResult),
	CountOf(Vec<Option<RuleResult>>),
	Both((Box<RuleResult>, Box<RuleResult>)),
	Either((Option<Box<RuleResult>>, Option<Box<RuleResult>>)),
	Given(GivenResult),
	Do,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RequirementResult {}

/// The "None" variant here represents Given rules with no `what` line
#[derive(Debug, Clone, PartialEq)]
pub struct GivenResult(Option<Vec<GivenOutput>>);

#[derive(Debug, Clone, PartialEq)]
pub struct AreaDescriptor {
	catalog: String,
	name: String,
	kind: String,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub enum GivenOutput {
	Course(CourseInstance),
	Credit((i16, i16)),
	Department(String),
	Term(i64),
	Grade((i16, i16)),
	AreaOfStudy(AreaDescriptor),
}

impl RuleResult {
	pub fn fail(detail: &RuleResultDetails) -> RuleResult {
		RuleResult {
			detail: detail.clone(),
			reservations: ReservedPairings::new(),
			status: RuleStatus::Fail,
		}
	}

	pub fn skip(detail: &RuleResultDetails) -> RuleResult {
		RuleResult {
			detail: detail.clone(),
			reservations: ReservedPairings::new(),
			status: RuleStatus::Skipped,
		}
	}

	pub fn is_pass(&self) -> bool {
		match self.status {
			RuleStatus::Pass => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn is_fail(&self) -> bool {
		match self.status {
			RuleStatus::Fail => true,
			_ => false,
		}
	}
}

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub enum RuleStatus {
	Pass,
	Fail,
	Skipped,
	#[allow(dead_code)]
	Pending,
}
