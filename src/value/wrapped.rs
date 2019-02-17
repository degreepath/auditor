use super::{SingleValue, TaggedValue};
use crate::filterable_data::DataValue;
use crate::traits::print;
use crate::util::{self, Oxford};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum WrappedValue {
	Single(TaggedValue),
	Or(Vec<TaggedValue>),
	And(Vec<TaggedValue>),
}

impl WrappedValue {
	pub fn new(s: &str) -> Self {
		WrappedValue::Single(TaggedValue::EqualTo(SingleValue::String(s.to_string())))
	}

	pub fn eq_string(s: &str) -> Self {
		WrappedValue::Single(TaggedValue::eq_string(s))
	}

	// TODO: remove this method
	pub fn is_true(&self) -> bool {
		match &self {
			WrappedValue::Single(val) => val.is_true(),
			_ => false,
		}
	}
}

impl print::Print for WrappedValue {
	fn print(&self) -> print::Result {
		use WrappedValue::{And, Or, Single};

		match &self {
			Single(v) => v.print(),
			Or(v) | And(v) => {
				let v: Vec<String> = v
					.iter()
					.filter_map(|r| match r.print() {
						Ok(p) => Some(p),
						Err(_) => None,
					})
					.collect();

				match &self {
					Or(_) => Ok(v.oxford("or")),
					And(_) => Ok(v.oxford("and")),
					_ => panic!("we already checked for Single"),
				}
			}
		}
	}
}

impl FromStr for WrappedValue {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let parts: Vec<_> = s.split(" | ").collect();

		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());
			for part in parts {
				tagged.push(part.parse::<TaggedValue>()?);
			}

			return Ok(WrappedValue::Or(tagged));
		}

		let parts: Vec<_> = s.split(" & ").collect();
		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());
			for part in parts {
				tagged.push(part.parse::<TaggedValue>()?);
			}

			return Ok(WrappedValue::And(tagged));
		}

		Ok(WrappedValue::Single(s.parse::<TaggedValue>()?))
	}
}

impl fmt::Display for WrappedValue {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		use WrappedValue::{And, Or, Single};

		let desc = match &self {
			Single(val) => format!("{}", val),
			And(values) | Or(values) => {
				let parts: Vec<_> = values.iter().map(|v| format!("{}", v)).collect();

				match &self {
					And(_) => parts.join(" & "),
					Or(_) => parts.join(" | "),
					_ => panic!("we already checked for Single"),
				}
			}
		};
		fmt.write_str(&desc)
	}
}

impl PartialEq<DataValue> for WrappedValue {
	fn eq(&self, rhs: &DataValue) -> bool {
		use DataValue::*;

		match rhs {
			Boolean(rhs) => match &self {
				WrappedValue::Single(value) => value == rhs,
				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
			},
			String(rhs) => match &self {
				WrappedValue::Single(value) => value == rhs,
				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
			},
			Integer(rhs) => match &self {
				WrappedValue::Single(value) => value == rhs,
				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
			},
			Float((a, b)) => match &self {
				WrappedValue::Single(value) => *value == (*a, *b),
				WrappedValue::Or(vec) => vec.iter().any(|v| *v == (*a, *b)),
				WrappedValue::And(vec) => vec.iter().all(|v| *v == (*a, *b)),
			},
			Vec(rhs) => match &self {
				WrappedValue::Single(value) => rhs.iter().any(|v| *value == *v),
				WrappedValue::Or(_vec) => {
					// I think this is going to want to convert them both to HashSets and
					// run an intersection on them?
					unimplemented!("'vec' data-value and 'or' wrapped-value")
				}
				WrappedValue::And(_vec) => unimplemented!("'vec' data-value and 'and' wrapped-value"),
			},
			Map(_rhs) => unimplemented!("'map' data-value compared to wrapped-value"),
			DateTime(_rhs) => unimplemented!("'datetime' data-value compared to wrapped-value"),
		}
	}
}

impl PartialEq<bool> for WrappedValue {
	fn eq(&self, rhs: &bool) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<String> for WrappedValue {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<str> for WrappedValue {
	fn eq(&self, rhs: &str) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<u64> for WrappedValue {
	fn eq(&self, rhs: &u64) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<(u16, u16)> for WrappedValue {
	fn eq(&self, rhs: &(u16, u16)) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<WrappedValue> for bool {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<WrappedValue> for String {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<WrappedValue> for str {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<WrappedValue> for u64 {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<WrappedValue> for (u16, u16) {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<WrappedValue> for DataValue {
	fn eq(&self, rhs: &WrappedValue) -> bool {
		rhs == self
	}
}

/*
use crate::audit::MatchType;
impl WrappedValue {
	pub fn compare_to_slice(&self, available: &[DataValue]) -> MatchType<Vec<MatchType<DataValue>>> {
		use std::collections::HashSet;

		match &self {
			WrappedValue::Single(needed) => {
				let found = available.iter().find(|item| needed == *item);
				match found {
					Some(item) => MatchType::Match(vec![MatchType::Match(item.clone())]),
					None => MatchType::Fail,
				}
			}
			WrappedValue::Or(possible) => {
				if possible.is_empty() {
					return MatchType::Skip;
				}

				let available: HashSet<_> = available.iter().map(|v| TaggedValue::eq_value(v)).collect();
				let possible: HashSet<_> = possible.iter().cloned().collect();

				let overlap: Vec<_> = available
					.intersection(&possible)
					.map(|v| match v {
						TaggedValue::EqualTo(v @ SingleValue::String(s)) => MatchType::Match(v.clone()),
						_ => unimplemented!(),
					})
					.collect();

				if overlap.is_empty() {
					MatchType::Fail
				} else {
					MatchType::Match(overlap)
				}
			}
			WrappedValue::And(needed) => {
				if needed.is_empty() {
					return MatchType::Skip;
				}

				let available: HashSet<_> = available.iter().map(|v| TaggedValue::eq_value(v)).collect();
				let needed: HashSet<_> = needed.iter().cloned().collect();

				let overlap: Vec<_> = available
					.union(&needed)
					.map(|v| match v {
						TaggedValue::EqualTo(SingleValue::String(s)) => MatchType::Match(s.clone()),
						_ => unimplemented!(),
					})
					.collect();

				if overlap.is_empty() || overlap.len() != needed.len() {
					MatchType::Fail
				} else {
					MatchType::Match(overlap)
				}
			}
		}
	}
}
*/
