use super::TaggedValue;
use crate::traits::print;
use crate::util::{self, Oxford};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum WrappedValue<T> {
	Single(TaggedValue<T>),
	Or(Vec<TaggedValue<T>>),
	And(Vec<TaggedValue<T>>),
}

impl WrappedValue<String> {
	pub fn new(s: &str) -> Self {
		WrappedValue::Single(TaggedValue::EqualTo(s.to_string()))
	}
}

impl<T: FromStr> FromStr for WrappedValue<T> {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let parts: Vec<_> = s.split(" | ").collect();

		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());

			for part in parts {
				tagged.push(part.parse::<TaggedValue<T>>()?);
			}

			return Ok(WrappedValue::Or(tagged));
		}

		let parts: Vec<_> = s.split(" & ").collect();
		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());

			for part in parts {
				tagged.push(part.parse::<TaggedValue<T>>()?);
			}

			return Ok(WrappedValue::And(tagged));
		}

		Ok(WrappedValue::Single(s.parse::<TaggedValue<T>>()?))
	}
}

impl<T: print::Print> print::Print for WrappedValue<T> {
	fn print(&self) -> print::Result {
		use WrappedValue::{And, Or, Single};

		match &self {
			Single(v) => v.print(),
			Or(v) | And(v) => {
				let v: Vec<String> = v.iter().filter_map(|r| r.print().ok()).collect();

				match &self {
					Or(_) => Ok(v.oxford("or")),
					And(_) => Ok(v.oxford("and")),
					_ => panic!("we already checked for Single"),
				}
			}
		}
	}
}

impl<T: fmt::Display> fmt::Display for WrappedValue<T> {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		use WrappedValue::{And, Or, Single};

		let desc = match &self {
			Single(val) => format!("{}", val),
			And(values) => {
				let parts: Vec<_> = values.iter().map(|v| format!("{}", v)).collect();
				parts.join(" & ")
			}
			Or(values) => {
				let parts: Vec<_> = values.iter().map(|v| format!("{}", v)).collect();
				parts.join(" | ")
			}
		};

		fmt.write_str(&desc)
	}
}

// impl<T> PartialEq<DataValue> for WrappedValue<T> {
// 	fn eq(&self, rhs: &DataValue) -> bool {
// 		use DataValue::*;

// 		match rhs {
// 			Boolean(rhs) => match &self {
// 				WrappedValue::Single(value) => value == rhs,
// 				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 			},
// 			String(rhs) => match &self {
// 				WrappedValue::Single(value) => value == rhs,
// 				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 			},
// 			Integer(rhs) => match &self {
// 				WrappedValue::Single(value) => value == rhs,
// 				WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 				WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 			},
// 			Float((a, b)) => match &self {
// 				WrappedValue::Single(value) => *value == (*a, *b),
// 				WrappedValue::Or(vec) => vec.iter().any(|v| *v == (*a, *b)),
// 				WrappedValue::And(vec) => vec.iter().all(|v| *v == (*a, *b)),
// 			},
// 			Vec(rhs) => match &self {
// 				WrappedValue::Single(value) => rhs.iter().any(|v| *value == *v),
// 				WrappedValue::Or(_vec) => {
// 					// I think this is going to want to convert them both to HashSets and
// 					// run an intersection on them?
// 					unimplemented!("'vec' data-value and 'or' wrapped-value")
// 				}
// 				WrappedValue::And(_vec) => unimplemented!("'vec' data-value and 'and' wrapped-value"),
// 			},
// 			Map(_rhs) => unimplemented!("'map' data-value compared to wrapped-value"),
// 			DateTime(_rhs) => unimplemented!("'datetime' data-value compared to wrapped-value"),
// 		}
// 	}
// }

// impl<T> PartialEq<bool> for WrappedValue<T> {
// 	fn eq(&self, rhs: &bool) -> bool {
// 		match &self {
// 			WrappedValue::Single(value) => value == rhs,
// 			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 		}
// 	}
// }

// impl<T> PartialEq<String> for WrappedValue<T> {
// 	fn eq(&self, rhs: &String) -> bool {
// 		match &self {
// 			WrappedValue::Single(value) => value == rhs,
// 			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 		}
// 	}
// }

// impl<T> PartialEq<str> for WrappedValue<T> {
// 	fn eq(&self, rhs: &str) -> bool {
// 		match &self {
// 			WrappedValue::Single(value) => value == rhs,
// 			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 		}
// 	}
// }

// impl<T> PartialEq<u64> for WrappedValue<T> {
// 	fn eq(&self, rhs: &u64) -> bool {
// 		match &self {
// 			WrappedValue::Single(value) => value == rhs,
// 			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 		}
// 	}
// }

// impl<T> PartialEq<(u16, u16)> for WrappedValue<T> {
// 	fn eq(&self, rhs: &(u16, u16)) -> bool {
// 		match &self {
// 			WrappedValue::Single(value) => value == rhs,
// 			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
// 			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
// 		}
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for bool {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for String {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for str {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for u64 {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for (u16, u16) {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }

// impl<T> PartialEq<WrappedValue<T>> for DataValue {
// 	fn eq(&self, rhs: &WrappedValue<T>) -> bool {
// 		rhs == self
// 	}
// }
