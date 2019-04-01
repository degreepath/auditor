use crate::rules::Rule as AnyRule;
use crate::traits::Util;
use serde::{Deserialize, Serialize};

mod counter;
mod print;
#[cfg(test)]
mod tests;

pub(crate) use counter::Counter;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub count: Counter,
	pub of: Vec<AnyRule>,
}

impl Rule {
	pub fn count_as_int(&self) -> u64 {
		match self.count {
			Counter::All => self.of.len() as u64,
			Counter::Any => 1,
			Counter::Number(n) => n,
		}
	}

	fn is_all(&self) -> bool {
		match self.count {
			Counter::All => true,
			Counter::Number(n) if n == self.of.len() as u64 => true,
			_ => false,
		}
	}

	fn is_any(&self) -> bool {
		match self.count {
			Counter::Any => true,
			Counter::Number(n) if n == 1 => true,
			_ => false,
		}
	}

	fn is_optional(&self) -> bool {
		match self.count {
			Counter::Number(0) => true,
			_ => false,
		}
	}

	fn is_single(&self) -> bool {
		self.of.len() == 1
	}

	fn is_either(&self) -> bool {
		self.of.len() == 2 && self.is_any()
	}

	fn is_both(&self) -> bool {
		self.of.len() == 2 && self.is_all()
	}

	fn only_requirements(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Requirement(_) => true,
			_ => false,
		})
	}

	fn only_courses(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Course(_) => true,
			_ => false,
		})
	}

	fn only_courses_and_requirements(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Requirement(_) | AnyRule::Course(_) => true,
			_ => false,
		})
	}

	fn should_be_inline(&self) -> bool {
		self.of.len() < 4 && !self.has_save_rule()
	}
}

impl Rule {
	fn to_both(&self) -> crate::rules::both::Rule {
		crate::rules::both::Rule {
			both: (Box::new(self.of[0].clone()), Box::new(self.of[1].clone())),
		}
	}

	fn to_either(&self) -> crate::rules::either::Rule {
		crate::rules::either::Rule {
			either: (Box::new(self.of[0].clone()), Box::new(self.of[1].clone())),
		}
	}
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		self.of.iter().any(|r| r.has_save_rule())
	}
}
