use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::ops::Deref;

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize, Hash)]
pub struct FilterableData(BTreeMap<String, DataValue>);

impl FilterableData {
	pub fn new(map: BTreeMap<String, DataValue>) -> FilterableData {
		FilterableData(map)
	}
}

impl Deref for FilterableData {
	type Target = BTreeMap<String, DataValue>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize, Hash)]
pub enum DataValue {
	Boolean(bool),
	String(String),
	Integer(u64),
	Float((u16, u16)),
	Vec(Vec<DataValue>),
	Map(BTreeMap<String, DataValue>),
	DateTime(chrono::DateTime<chrono::Utc>),
}

impl From<f32> for DataValue {
	fn from(num: f32) -> DataValue {
		DataValue::Float((num.trunc() as u16, (num.fract() * 100.0) as u16))
	}
}

impl PartialEq<bool> for DataValue {
	fn eq(&self, rhs: &bool) -> bool {
		match &self {
			DataValue::Boolean(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<String> for DataValue {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			DataValue::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<str> for DataValue {
	fn eq(&self, rhs: &str) -> bool {
		match &self {
			DataValue::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<u64> for DataValue {
	fn eq(&self, rhs: &u64) -> bool {
		match &self {
			DataValue::Integer(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<(u16, u16)> for DataValue {
	fn eq(&self, rhs: &(u16, u16)) -> bool {
		match &self {
			DataValue::Float(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<u16> for DataValue {
	fn eq(&self, rhs: &u16) -> bool {
		match &self {
			DataValue::Integer(lhs) => *lhs == *rhs as u64,
			_ => false,
		}
	}
}

impl PartialEq<f32> for DataValue {
	fn eq(&self, rhs: &f32) -> bool {
		self == &DataValue::from(*rhs)
	}
}

impl PartialEq<DataValue> for bool {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for String {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for str {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for u64 {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for u16 {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for f32 {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}

impl PartialEq<DataValue> for (u16, u16) {
	fn eq(&self, rhs: &DataValue) -> bool {
		rhs == self
	}
}
