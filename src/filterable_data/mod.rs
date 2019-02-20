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

impl From<BTreeMap<String, DataValue>> for FilterableData {
	fn from(map: BTreeMap<String, DataValue>) -> Self {
		FilterableData(map)
	}
}

impl From<BTreeMap<&str, DataValue>> for FilterableData {
	fn from(map: BTreeMap<&str, DataValue>) -> Self {
		FilterableData(map.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
	}
}

impl From<BTreeMap<&str, &str>> for FilterableData {
	fn from(map: BTreeMap<&str, &str>) -> Self {
		FilterableData(
			map.into_iter()
				.map(|(k, v)| (k.to_string(), DataValue::from(v)))
				.collect(),
		)
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

impl From<&str> for DataValue {
	fn from(s: &str) -> DataValue {
		DataValue::String(s.to_string())
	}
}

impl From<u64> for DataValue {
	fn from(n: u64) -> DataValue {
		DataValue::Integer(n)
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
			DataValue::Integer(lhs) => *lhs == u64::from(*rhs),
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
