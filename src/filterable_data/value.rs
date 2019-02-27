use chrono::{DateTime, Utc};
use serde::Serialize;
use std::collections::BTreeMap;

mod deserialize;
mod from;
mod partialeq;

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Hash)]
pub enum DataValue {
	Boolean(bool),
	String(String),
	Integer(u64),
	Float((u16, u16)),
	Vec(Vec<DataValue>),
	Map(BTreeMap<String, DataValue>),
	DateTime(DateTime<Utc>),
}

pub type Sequence = Vec<DataValue>;
pub type Mapping = BTreeMap<String, DataValue>;

impl DataValue {
	pub fn is_bool(&self) -> bool {
		self.as_bool().is_some()
	}

	pub fn as_bool(&self) -> Option<bool> {
		match *self {
			DataValue::Boolean(b) => Some(b),
			_ => None,
		}
	}

	pub fn is_number(&self) -> bool {
		match *self {
			DataValue::Integer(_) | DataValue::Float(_) => true,
			_ => false,
		}
	}

	pub fn is_integer(&self) -> bool {
		self.as_integer().is_some()
	}

	pub fn as_integer(&self) -> Option<u64> {
		match *self {
			DataValue::Integer(n) => Some(n),
			_ => None,
		}
	}

	pub fn is_float(&self) -> bool {
		self.as_float().is_some()
	}

	pub fn as_float(&self) -> Option<(u16, u16)> {
		match *self {
			DataValue::Float((i, r)) => Some((i, r)),
			_ => None,
		}
	}

	pub fn is_string(&self) -> bool {
		self.as_string().is_some()
	}

	pub fn as_string(&self) -> Option<String> {
		match &self {
			DataValue::String(s) => Some(s.clone()),
			_ => None,
		}
	}

	pub fn is_vec(&self) -> bool {
		self.as_vec().is_some()
	}

	pub fn as_vec(&self) -> Option<&Sequence> {
		match *self {
			DataValue::Vec(ref seq) => Some(seq),
			_ => None,
		}
	}

	pub fn as_vec_mut(&mut self) -> Option<&mut Sequence> {
		match *self {
			DataValue::Vec(ref mut seq) => Some(seq),
			_ => None,
		}
	}

	pub fn is_mapping(&self) -> bool {
		self.as_mapping().is_some()
	}

	pub fn as_mapping(&self) -> Option<&Mapping> {
		match *self {
			DataValue::Map(ref map) => Some(map),
			_ => None,
		}
	}

	pub fn as_mapping_mut(&mut self) -> Option<&mut Mapping> {
		match *self {
			DataValue::Map(ref mut map) => Some(map),
			_ => None,
		}
	}
}
