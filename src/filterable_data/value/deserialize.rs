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
