use super::Clause;
use super::WrappedValue;
use crate::util;
use indexmap::IndexMap;
use serde::de::Deserializer;
use serde::Deserialize;

pub fn deserialize_with<'de, D>(deserializer: D) -> Result<Option<Clause>, D::Error>
where
	D: Deserializer<'de>,
{
	#[derive(Deserialize)]
	// TODO: support integers and booleans as well as string/struct
	struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] WrappedValue);

	// TODO: improve this to not transmute the hashmap right after creation
	let v: Result<IndexMap<String, Wrapper>, D::Error> = IndexMap::deserialize(deserializer);

	match v {
		Ok(v) => {
			let transmuted: Clause = v.into_iter().map(|(k, v)| (k, v.0)).collect();
			Ok(Some(transmuted))
		}
		Err(err) => Err(err),
	}
}

pub fn deserialize_with_no_option<'de, D>(deserializer: D) -> Result<Clause, D::Error>
where
	D: Deserializer<'de>,
{
	#[derive(Deserialize)]
	// TODO: support integers and booleans as well as string/struct
	struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] WrappedValue);

	// TODO: improve this to not transmute the hashmap right after creation
	let v: Result<IndexMap<String, Wrapper>, D::Error> = IndexMap::deserialize(deserializer);

	match v {
		Ok(v) => {
			let transmuted: Clause = v.into_iter().map(|(k, v)| (k, v.0)).collect();
			Ok(transmuted)
		}
		Err(err) => Err(err),
	}
}
