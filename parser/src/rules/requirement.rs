use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
	pub requirement: String,
	#[serde(default = "util::serde_false")]
	pub optional: bool,
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

		write!(&mut output, "“{}”", self.requirement)?;

		if self.optional == true {
			write!(&mut output, " (optional)")?;
		}

		Ok(output)
	}
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize() {
		let data = Rule {
			requirement: String::from("Name"),
			optional: false,
		};
		let expected = "---
requirement: Name
optional: false";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize() {
		let data = "---
requirement: Name
optional: false";
		let expected = Rule {
			requirement: String::from("Name"),
			optional: false,
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_with_defaults() {
		let data = "---
requirement: Name";
		let expected = Rule {
			requirement: String::from("Name"),
			optional: false,
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;

		let input = Rule {
			requirement: "Core".into(),
			optional: false,
		};
		let expected = "“Core”";
		assert_eq!(expected, input.print().unwrap());

		let input = Rule {
			requirement: "Core".into(),
			optional: true,
		};
		let expected = "“Core” (optional)";
		assert_eq!(expected, input.print().unwrap());
	}
}
