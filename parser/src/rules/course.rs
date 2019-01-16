use crate::util;
use serde::ser::{Serialize, SerializeStruct, Serializer};
use std::str::FromStr;
use void::Void;

#[derive(Default, Debug, PartialEq, Clone, Deserialize)]
pub struct Rule {
	pub course: String,
	pub term: Option<String>,
	pub section: Option<String>,
	pub year: Option<u64>,
	pub semester: Option<String>,
	pub lab: Option<bool>,
	pub international: Option<bool>,
}

impl crate::rules::traits::RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		false
	}
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use std::fmt::Write;
		let mut output = String::new();

		write!(&mut output, "{}", self.course)?;

		if let Some(section) = &self.section {
			write!(&mut output, "{}", section)?;
		}

		let mut annotations = match (&self.term, self.year, &self.semester) {
			(Some(term), None, None) => Some(format!("{}", util::pretty_term(&term))),
			(None, Some(year), None) => Some(format!("{}", util::expand_year(year, "dual"))),
			(None, None, Some(semester)) => Some(format!("{}", semester)),
			(None, Some(year), Some(semester)) => Some(format!("{} {}", semester, util::expand_year(year, "short"))),
			(Some(_), Some(_), _) | (Some(_), _, Some(_)) => unimplemented!(),
			(None, None, None) => None,
		};

		match (self.lab, &annotations) {
			(Some(lab), Some(ant)) if lab == true => {
				annotations = Some(format!("Lab; {}", ant));
			}
			(Some(lab), None) if lab == true => {
				annotations = Some("Lab".to_string());
			}
			_ => (),
		}

		match (self.international, &annotations) {
			(Some(intl), Some(ant)) if intl == true => {
				annotations = Some(format!("International; {}", ant));
			}
			(Some(intl), None) if intl == true => {
				annotations = Some("International".to_string());
			}
			_ => (),
		}

		if let Some(annotations) = annotations {
			write!(&mut output, " ({})", annotations)?;
		}

		Ok(output)
	}
}

impl FromStr for Rule {
	// This implementation of `from_str` can never fail, so use the impossible
	// `Void` type as the error type.
	type Err = Void;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		Ok(Rule {
			course: String::from(s),
			..Default::default()
		})
	}
}

impl Serialize for Rule {
	fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
	where
		S: Serializer,
	{
		match &self {
			Rule {
				term: None,
				section: None,
				year: None,
				semester: None,
				lab: None,
				international: None,
				course,
			} => {
				let mut state = serializer.serialize_struct("Rule", 1)?;
				state.serialize_field("course", course)?;
				state.end()
			}
			_ => {
				let mut state = serializer.serialize_struct("Rule", 7)?;
				state.serialize_field("course", &self.course)?;
				state.serialize_field("term", &self.term)?;
				state.serialize_field("section", &self.section)?;
				state.serialize_field("year", &self.year)?;
				state.serialize_field("semester", &self.semester)?;
				state.serialize_field("lab", &self.lab)?;
				state.serialize_field("international", &self.international)?;
				state.end()
			}
		}
	}
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize() {
		let data = Rule {
			course: "STAT 214".to_string(),
			..Default::default()
		};

		let expected_str = "---
course: STAT 214";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected_str);
	}

	#[test]
	fn serialize_expanded() {
		let data = Rule {
			course: "STAT 214".to_string(),
			term: Some("2014-4".to_string()),
			..Default::default()
		};

		let expected_str = "---
course: STAT 214
term: 2014-4
section: ~
year: ~
semester: ~
lab: ~
international: ~";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected_str);

		let deserialized: Rule = serde_yaml::from_str(&actual).unwrap();
		assert_eq!(deserialized, data);
	}

	#[test]
	fn deserialize_labelled() {
		let data = "---
course: STAT 214";

		let expected_struct = Rule {
			course: "STAT 214".to_string(),
			..Default::default()
		};

		let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(deserialized, expected_struct);
	}

	#[test]
	fn deserialize_expanded() {
		let data = "---
course: STAT 214
term: 2014-4
section: ~
year: ~
semester: ~
lab: ~
international: ~";

		let expected_struct = Rule {
			course: "STAT 214".to_string(),
			term: Some("2014-4".to_string()),
			..Default::default()
		};

		let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(deserialized, expected_struct);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;

		let input = Rule {
			course: "DEPT 111".into(),
			..Default::default()
		};
		let expected = "DEPT 111";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			semester: Some("Fall".to_string()),
			year: Some(2015),
			..Default::default()
		};
		let expected = "DEPT 111 (Fall 2015)";
		assert_eq!(expected, input.print().unwrap());

		// TODO: implement term parsing to get to this point `let expected = "DEPT 111 (Fall 2015)";`
		let input = Rule {
			course: "DEPT 111".into(),
			term: Some("2015-1".to_string()),
			..Default::default()
		};
		let expected = "DEPT 111 (2015-1)";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			semester: Some("Fall".to_string()),
			..Default::default()
		};
		let expected = "DEPT 111 (Fall)";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			year: Some(2015),
			..Default::default()
		};
		let expected = "DEPT 111 (2015-16)";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			section: Some("A".to_string()),
			..Default::default()
		};
		let expected = "DEPT 111A";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			lab: Some(true),
			..Default::default()
		};
		let expected = "DEPT 111 (Lab)";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			semester: Some("Fall".to_string()),
			year: Some(2015),
			lab: Some(true),
			..Default::default()
		};
		let expected = "DEPT 111 (Lab; Fall 2015)";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			course: "DEPT 111".into(),
			section: Some("A".to_string()),
			semester: Some("Fall".to_string()),
			year: Some(2015),
			lab: Some(true),
			international: Some(true),
			term: None,
		};
		let expected = "DEPT 111A (International; Lab; Fall 2015)";
		assert_eq!(expected, input.print().unwrap());
	}
}
