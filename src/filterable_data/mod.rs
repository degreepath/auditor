use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::ops::Deref;

mod value;

pub use value::DataValue;

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize, Hash)]
pub struct FilterableData(BTreeMap<String, DataValue>);

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
