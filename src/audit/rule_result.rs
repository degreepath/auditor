use super::ReservedPairings;
use crate::student::{AreaDescriptor, CourseInstance};

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
	/// The "None" variant here represents Given rules with no `what` line
	Given(GivenOutputType),
	Do,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RequirementResult {}

#[derive(Debug, Clone, PartialEq)]
pub enum GivenOutputType {
	Count(u64),
	SumInteger(u64),
	SumFloat(f32),
	Average(f32),
	Max(Box<Option<GivenOutput>>),
	Min(Box<Option<GivenOutput>>),
	MultiValue(Vec<GivenOutput>),
	None,
}

#[derive(Debug, Clone, PartialEq)]
pub enum GivenOutput {
	Course(CourseInstance),
	Credit(f32),
	Department(String),
	Term(u64),
	Grade(f32),
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
