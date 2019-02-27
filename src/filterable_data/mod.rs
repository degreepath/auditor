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

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Hash)]
pub enum DataValue {
	Boolean(bool),
	String(String),
	Integer(u64),
	Float((u16, u16)),
	Vec(Vec<DataValue>),
	Map(BTreeMap<String, DataValue>),
	DateTime(chrono::DateTime<chrono::Utc>),
}

mod datavalue_deserialize {
	use super::DataValue;
	use chrono::{DateTime, Utc};
	use serde::de::{self, MapAccess, SeqAccess, Visitor};
	use serde::{Deserialize, Deserializer};
	use std::collections::BTreeMap;
	use std::fmt;

	struct DataValueVisitor;

	impl<'de> Visitor<'de> for DataValueVisitor {
		type Value = DataValue;

		fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
			formatter.write_str("a piece of data")
		}

		fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E>
		where
			E: de::Error,
		{
			if value >= 0 {
				Ok(DataValue::Integer(value as u64))
			} else {
				Err(E::custom(format!("i64 out of range: {}", value)))
			}
		}

		fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E>
		where
			E: de::Error,
		{
			Ok(DataValue::Integer(value))
		}

		fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
		where
			E: de::Error,
		{
			Ok((value as f32).into())
		}

		fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E>
		where
			E: de::Error,
		{
			Ok(DataValue::Boolean(value))
		}

		fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
		where
			E: de::Error,
		{
			if value.contains('T') {
				// might be a date
				match DateTime::parse_from_rfc3339(&value) {
					Ok(date) => Ok(DataValue::DateTime(date.with_timezone(&Utc))),
					Err(_) => Ok(DataValue::String(value.to_string())),
				}
			} else {
				// definitely not a date
				Ok(DataValue::String(value.to_string()))
			}
		}

		fn visit_seq<S>(self, mut visitor: S) -> Result<Self::Value, S::Error>
		where
			S: SeqAccess<'de>,
		{
			let mut vec = Vec::new();

			while let Some(element) = visitor.next_element()? {
				vec.push(element);
			}

			Ok(DataValue::Vec(vec))
		}

		fn visit_map<M>(self, mut visitor: M) -> Result<Self::Value, M::Error>
		where
			M: MapAccess<'de>,
		{
			let mut values = BTreeMap::new();

			while let Some((key, value)) = visitor.next_entry()? {
				values.insert(key, value);
			}

			Ok(DataValue::Map(values))
		}
	}

	impl<'de> Deserialize<'de> for DataValue {
		fn deserialize<D>(deserializer: D) -> Result<DataValue, D::Error>
		where
			D: Deserializer<'de>,
		{
			deserializer.deserialize_any(DataValueVisitor)
		}
	}
}

impl DataValue {
	pub fn to_string(&self) -> Option<String> {
		match &self {
			DataValue::String(s) => Some(s.to_string()),
			_ => None,
		}
	}
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
