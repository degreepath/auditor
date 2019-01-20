use crate::filter;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	#[serde(rename = "where", deserialize_with = "filter::deserialize_with_no_option")]
	filter: filter::Clause,
	at_most: u64,
}
