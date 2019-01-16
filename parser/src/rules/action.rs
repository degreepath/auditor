use crate::rules::given::action::Action;
use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
	#[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
	pub action: Action,
}

impl crate::rules::traits::RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		true
	}
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use crate::rules::given::action::Operator;
		use std::fmt::Write;

		let mut output = String::new();
		let action = &self.action;

		match (&action.lhs, &action.op, &action.rhs) {
			(lhs, Some(op), Some(rhs)) => {
				let op = match op {
					Operator::LessThan => "less than",
					Operator::LessThanEqualTo => "less most or equal to",
					Operator::EqualTo => "equal to",
					Operator::GreaterThan => "greater than",
					Operator::GreaterThanEqualTo => "greater than or equal to",
					Operator::NotEqualTo => "not equal to",
				};

				write!(
					&mut output,
					"ensure that the computed result of the subset “{}” is {} the computed result of the subset “{}”",
					lhs, op, rhs
				)?;
			}
			_ => panic!("invalid standalone do-rule"),
		}

		Ok(output)
	}
}

#[cfg(test)]
mod test {
	use super::*;
	use crate::rules::given::action;

	#[test]
	fn deserialize() {
		let data = r#"---
do: >
  "first BTS-T course" < "last EIN course""#;

		let expected_struct = Rule {
			action: Action {
				lhs: action::Value::String("first BTS-T course".to_string()),
				op: Some(action::Operator::LessThan),
				rhs: Some(action::Value::String("last EIN course".to_string())),
			},
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(expected_struct, actual);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;
		let data = r#"---
do: >
  "first BTS-T course" < "last EIN course""#;

		let expected = "ensure that the computed result of the subset “first BTS-T course” is less than the computed result of the subset “last EIN course”";

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(expected, actual.print().unwrap());
	}

	#[test]
	fn pretty_print_gte() {
		use crate::rules::traits::PrettyPrint;
		let data = r#"---
do: >
  "first BTS-T course" >= "last EIN course""#;

		let expected = "ensure that the computed result of the subset “first BTS-T course” is greater than or equal to the computed result of the subset “last EIN course”";

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(expected, actual.print().unwrap());
	}

	#[test]
	#[ignore]
	fn pretty_print_block() {
		use crate::rules::traits::PrettyPrint;

		let input: Rule = serde_yaml::from_str(
			&"---
given: these courses
courses: [DANCE 399]
where: {year: graduation-year, semester: Fall}
name: $dance_seminars
label: Senior Dance Seminars
",
		)
		.unwrap();
		let expected = "Given the intersection between the following potential courses and your transcript, but limiting your transcript to only the courses taken in the Fall of your Senior year, as “Senior Dance Seminars”:

| Potential | “Senior Dance Seminars” |
| --------- | ----------------------- |
| DANCE 399 | DANCE 399 2015-1        |";
		assert_eq!(expected, input.print().unwrap());
	}
}
