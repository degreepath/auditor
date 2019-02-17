use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::ops::Deref;

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize)]
pub struct FilterableData(BTreeMap<String, DataValue>);

impl Deref for FilterableData {
	type Target = BTreeMap<String, DataValue>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize)]
pub enum DataValue {
	String(String),
	Integer(u64),
	Float((u16, u16)),
	Vec(Vec<DataValue>),
	Map(BTreeMap<String, DataValue>),
	DateTime(chrono::DateTime<chrono::Utc>),
}
