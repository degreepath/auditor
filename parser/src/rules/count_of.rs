use crate::rules::traits::RuleTools;
use crate::rules::Rule as AnyRule;
use crate::util::Oxford;
use serde::de::{self, Deserialize, Deserializer, Visitor};
use serde::ser::{Serialize, Serializer};
use std::fmt;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub count: Counter,
	pub of: Vec<AnyRule>,
}

impl Rule {
	fn is_all(&self) -> bool {
		match self.count {
			Counter::All => true,
			Counter::Number(n) if n == self.of.len() as u64 => true,
			_ => false,
		}
	}

	fn is_any(&self) -> bool {
		match self.count {
			Counter::Any => true,
			Counter::Number(n) if n == 1 => true,
			_ => false,
		}
	}

	fn is_single(&self) -> bool {
		self.of.len() == 1
	}

	fn is_either(&self) -> bool {
		self.of.len() == 2 && self.is_any()
	}

	fn is_both(&self) -> bool {
		self.of.len() == 2 && self.is_all()
	}

	fn only_requirements(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Requirement(_) => true,
			_ => false,
		})
	}

	fn only_courses(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Course(_) => true,
			_ => false,
		})
	}

	fn only_courses_and_requirements(&self) -> bool {
		self.of.iter().all(|r| match r {
			AnyRule::Requirement(_) | AnyRule::Course(_) => true,
			_ => false,
		})
	}

	fn should_be_inline(&self) -> bool {
		self.of.len() < 4 && !self.has_save_rule()
	}
}

fn result_to_option<T, E>(r: Result<T, E>) -> Option<T> {
	match r {
		Ok(v) => Some(v),
		Err(_) => None,
	}
}

impl RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		self.of.iter().any(|r| r.has_save_rule())
		// AnyRule::Given(crate::rules::given::Rule {given: crate::rules::given::Given::NamedVariable {..}, ..}) => true,
	}
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use std::fmt::Write;

		if self.is_single() {
			let req = &self.of[0].print_inner()?;
			if self.only_requirements() {
				return Ok(format!("complete the {} requirement", req));
			} else if self.only_courses() {
				return Ok(format!("take {}", req));
			} else {
				return Ok(format!("{}", req));
			}
		}

		if self.is_either() {
			let either = crate::rules::either::Rule {
				either: (Box::new(self.of[0].clone()), Box::new(self.of[1].clone())),
			};
			return either.print();
		}

		if self.is_both() {
			let both = crate::rules::both::Rule {
				both: (Box::new(self.of[0].clone()), Box::new(self.of[1].clone())),
			};
			return both.print();
		}

		let mut output = String::new();

		fn print_and_collect(ref v: &[AnyRule]) -> Vec<String> {
			v.iter().map(|r| r.print_inner()).filter_map(result_to_option).collect()
		}

		fn print_and_collect_special_for_requirement(ref v: &[AnyRule]) -> Vec<String> {
			v.iter().map(|r| r.print()).filter_map(result_to_option).collect()
		}

		fn print_and_join_for_block_elided(ref v: &[AnyRule]) -> String {
			v.iter()
				.map(|r| r.print_inner())
				.filter_map(result_to_option)
				.map(|r| format!("- {}", r))
				.collect::<Vec<String>>()
				.join("\n")
		}

		fn print_and_join_for_block_verbose(ref v: &[AnyRule]) -> String {
			v.iter()
				.map(|r| r.print())
				.filter_map(result_to_option)
				.map(|r| format!("- {}", r))
				.collect::<Vec<String>>()
				.join("\n")
		}

		fn collect_and_sort_three_up(ref v: &[AnyRule]) -> (WhichUp, &AnyRule, &AnyRule, &AnyRule) {
			let a = &v[0];
			let b = &v[1];
			let c = &v[2];

			match v {
				[AnyRule::Course(_), AnyRule::Course(_), AnyRule::Requirement(_)] => (WhichUp::Course, a, b, c),
				[AnyRule::Course(_), AnyRule::Requirement(_), AnyRule::Course(_)] => (WhichUp::Course, a, c, b),
				[AnyRule::Requirement(_), AnyRule::Course(_), AnyRule::Course(_)] => (WhichUp::Course, b, c, a),
				[AnyRule::Course(_), AnyRule::Requirement(_), AnyRule::Requirement(_)] => {
					(WhichUp::Requirement, a, b, c)
				}
				[AnyRule::Requirement(_), AnyRule::Course(_), AnyRule::Requirement(_)] => {
					(WhichUp::Requirement, b, a, c)
				}
				[AnyRule::Requirement(_), AnyRule::Requirement(_), AnyRule::Course(_)] => {
					(WhichUp::Requirement, c, a, b)
				}
				_ => panic!("should only be triples of Course/Requirement, but was {:?}", v),
			}
		}

		// todo: move this elsewhere
		enum WhichUp {
			Course,
			Requirement,
		};

		// assert: 2 < len

		if self.is_any() {
			if self.should_be_inline() {
				// assert: 2 < len < 4
				if self.only_requirements() {
					let rules = print_and_collect(&self.of);

					write!(
						&mut output,
						"complete one requirement from among {}",
						rules.oxford("or")
					)?;
				} else if self.only_courses() {
					let rules = print_and_collect(&self.of);

					write!(&mut output, "take one course from among {}", rules.oxford("or"))?;
				} else if self.only_courses_and_requirements() {
					let (which_up, a, b, c) = collect_and_sort_three_up(&self.of);
					let a = a.print_inner()?;
					let b = b.print_inner()?;
					let c = c.print_inner()?;

					match which_up {
						WhichUp::Course => {
							write!(&mut output, "take {} or {}, or complete the {} requirement", a, b, c)?
						}
						WhichUp::Requirement => write!(
							&mut output,
							"take {}, or complete either the {} or {} requirements",
							a, b, c
						)?,
					};
				} else {
					// force block mode due to clarify of mixed types and "any"
					let rules = print_and_join_for_block_verbose(&self.of);

					write!(&mut output, "do any of the following:\n\n{}", rules)?;
				}
			} else {
				// assert: 4 < len
				if self.only_requirements() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(&mut output, "complete any of the following requirements:\n\n{}", rules)?;
				} else if self.only_courses() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(&mut output, "take any of the following courses:\n\n{}", rules)?;
				} else {
					let rules = print_and_join_for_block_verbose(&self.of);

					write!(&mut output, "do any of the following:\n\n{}", rules)?;
				}
			}
		} else if self.is_all() {
			if self.should_be_inline() {
				// assert: 2 < len < 4
				if self.only_requirements() {
					let rules = print_and_collect(&self.of);

					write!(&mut output, "complete {}", rules.oxford("and"))?;
				} else if self.only_courses() {
					let rules = print_and_collect(&self.of);

					write!(&mut output, "take {}", rules.oxford("and"))?;
				} else if self.only_courses_and_requirements() {
					let (which_up, a, b, c) = collect_and_sort_three_up(&self.of);
					let a = a.print_inner()?;
					let b = b.print_inner()?;
					let c = c.print_inner()?;

					match which_up {
						WhichUp::Course => {
							write!(&mut output, "take {} and {}, and complete the {} requirement", a, b, c)?
						}
						WhichUp::Requirement => write!(
							&mut output,
							"take {}, and complete both the {} and {} requirements",
							a, b, c
						)?,
					};
				} else {
					let rules = print_and_collect_special_for_requirement(&self.of);

					write!(&mut output, "{}", rules.oxford("and"))?;
				}
			} else {
				// assert: 4 < len
				if self.only_requirements() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(&mut output, "complete all of the following requirements:\n\n{}", rules)?;
				} else if self.only_courses() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(&mut output, "take all of the following courses:\n\n{}", rules)?;
				} else {
					let rules = print_and_join_for_block_verbose(&self.of);

					write!(&mut output, "do all of the following:\n\n{}", rules)?;
				}
			}
		} else {
			// numeric
			let n = self.count.english();

			if self.should_be_inline() {
				// assert: 2 < len < 4
				if self.only_requirements() {
					let rules = print_and_collect(&self.of);

					write!(
						&mut output,
						"complete {} requirements from among {}",
						n,
						rules.oxford("or")
					)?;
				} else if self.only_courses() {
					let rules = print_and_collect(&self.of);

					write!(&mut output, "take {} courses from among {}", n, rules.oxford("or"))?;
				} else if self.only_courses_and_requirements() {
					let (courses, reqs): (Vec<AnyRule>, Vec<AnyRule>) =
						self.of.clone().into_iter().partition(|r| match r {
							AnyRule::Course(_) => true,
							_ => false,
						});

					let mut rules: Vec<_> = vec![];
					rules.append(&mut print_and_collect(&courses));
					rules.append(&mut print_and_collect(&reqs));

					let rules = rules.oxford("or");

					write!(
						&mut output,
						"complete or take {} requirements or courses from among {}",
						n, rules
					)?;
				} else {
					// force block mode due to mixed content and numeric
					let rules = print_and_join_for_block_verbose(&self.of);

					write!(&mut output, "do {} from among the following:\n\n{}", n, rules)?;
				}
			} else {
				// assert: 4 < len
				if self.only_requirements() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(
						&mut output,
						"complete {} from among the following requirements:\n\n{}",
						n, rules
					)?;
				} else if self.only_courses() {
					let rules = print_and_join_for_block_elided(&self.of);

					write!(&mut output, "take {} from among the following courses:\n\n{}", n, rules)?;
				} else {
					let rules = print_and_join_for_block_verbose(&self.of);

					write!(&mut output, "do {} from among the following:\n\n{}", n, rules)?;
				}
			}
		}

		Ok(output)
	}
}

#[derive(Debug, PartialEq, Clone)]
pub enum Counter {
	All,
	Any,
	Number(u64),
}

impl Counter {
	fn english(&self) -> String {
		match &self {
			Counter::All => "all".to_string(),
			Counter::Any => "any".to_string(),
			Counter::Number(0) => "zero".to_string(),
			Counter::Number(1) => "one".to_string(),
			Counter::Number(2) => "two".to_string(),
			Counter::Number(3) => "three".to_string(),
			Counter::Number(4) => "four".to_string(),
			Counter::Number(5) => "five".to_string(),
			Counter::Number(6) => "six".to_string(),
			Counter::Number(7) => "seven".to_string(),
			Counter::Number(8) => "eight".to_string(),
			Counter::Number(9) => "nine".to_string(),
			Counter::Number(10) => "ten".to_string(),
			Counter::Number(n) => format!("{}", n),
		}
	}
}

impl fmt::Display for Counter {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		let what: String = match &self {
			Counter::All => "all".to_string(),
			Counter::Any => "any".to_string(),
			Counter::Number(n) => format!("{}", n),
		};
		fmt.write_str(&what)
	}
}

impl Serialize for Counter {
	fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
	where
		S: Serializer,
	{
		match &self {
			Counter::All => serializer.serialize_str("all"),
			Counter::Any => serializer.serialize_str("any"),
			Counter::Number(n) => serializer.serialize_u64(*n),
		}
	}
}

impl<'de> Deserialize<'de> for Counter {
	fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
	where
		D: Deserializer<'de>,
	{
		struct CountVisitor;

		impl<'de> Visitor<'de> for CountVisitor {
			type Value = Counter;

			fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
				f.write_str("`count` as a number, any, or all")
			}

			fn visit_i64<E>(self, num: i64) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				Err(E::custom(format!("negative numbers are not allowed; was `{}`", num)))
			}

			fn visit_u64<E>(self, num: u64) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				Ok(Counter::Number(num))
			}

			fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				match value {
					"all" => Ok(Counter::All),
					"any" => Ok(Counter::Any),
					_ => Err(E::custom(format!("string must be `any` or `all`; was `{}`", value))),
				}
			}
		}

		deserializer.deserialize_any(CountVisitor)
	}
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize_count_of_any() {
		let data = Rule {
			count: Counter::Any,
			of: vec![],
		};

		let expected_str = "---
count: any
of: []";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected_str);
	}

	#[test]
	fn deserialize_count_of_any() {
		let data = "---
count: any
of: []";

		let expected_struct = Rule {
			count: Counter::Any,
			of: vec![],
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected_struct);
	}

	#[test]
	fn serialize_count_of_all() {
		let data = Rule {
			count: Counter::All,
			of: vec![],
		};

		let expected_str = "---
count: all
of: []";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected_str);
	}

	#[test]
	fn deserialize_count_of_all() {
		let data = "---
count: all
of: []";

		let expected_struct = Rule {
			count: Counter::All,
			of: vec![],
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected_struct);
	}

	#[test]
	fn serialize_count_of_number() {
		let data = Rule {
			count: Counter::Number(6),
			of: vec![],
		};

		let expected_str = "---
count: 6
of: []";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected_str);
	}

	#[test]
	fn deserialize_count_of_number() {
		let data = "---
count: 6
of: []";

		let expected_struct = Rule {
			count: Counter::Number(6),
			of: vec![],
		};

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected_struct);
	}

	#[test]
	fn pretty_print_inline() {
		use crate::rules::traits::PrettyPrint;

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111]}").unwrap();
		let expected = "take CS 111";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: Core}]}").unwrap();
		let expected = "complete the “Core” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [{both: [CS 111, CS 121]}]}").unwrap();
		let expected = "take both CS 111 and CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121]}").unwrap();
		let expected = "take both CS 111 and CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121]}").unwrap();
		let expected = "take either CS 111 or CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, CS 131]}").unwrap();
		let expected = "take one course from among CS 111, CS 121, or CS 131";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, CS 131]}").unwrap();
		let expected = "take CS 111, CS 121, and CS 131";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}]}").unwrap();
		let expected = "complete both the “A” and “B” requirements";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
		let expected = "complete “A”, “B”, and “C”";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
		let expected = "complete one requirement from among “A”, “B”, or “C”";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
		let expected = "complete two requirements from among “A”, “B”, or “C”";
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn all_two_course_one_requirement() {
		use crate::rules::traits::PrettyPrint;
		let expected = "take CS 111 and CS 121, and complete the “B” requirement";

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, {requirement: B}, CS 121]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: B}, CS 111, CS 121]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn any_two_course_one_requirement() {
		use crate::rules::traits::PrettyPrint;
		let expected = "take CS 111 or CS 121, or complete the “B” requirement";

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, {requirement: B}, CS 121]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: B}, CS 111, CS 121]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn all_two_requirement_one_course() {
		use crate::rules::traits::PrettyPrint;
		let expected = "take CS 111, and complete both the “A” and “B” requirements";

		let input: Rule =
			serde_yaml::from_str(&"{count: all, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: all, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn any_two_requirement_one_course() {
		use crate::rules::traits::PrettyPrint;
		let expected = "take CS 111, or complete either the “A” or “B” requirements";

		let input: Rule =
			serde_yaml::from_str(&"{count: any, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: any, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: any, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn two_of_one_requirement_two_course() {
		use crate::rules::traits::PrettyPrint;
		let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn two_of_two_requirement_one_course() {
		use crate::rules::traits::PrettyPrint;
		let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn both_either_requirement() {
		use crate::rules::traits::PrettyPrint;

		let input: Rule =
            serde_yaml::from_str(&"{count: all, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}").unwrap();
		let expected = "take both CS 111 and CS 251, complete either the “A” or “B” requirement, and complete the “C” requirement";
		assert_eq!(expected, input.print().unwrap());
	}

	#[test]
	fn pretty_print_block() {
		use crate::rules::traits::PrettyPrint;

		let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
		let expected = "take any of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: 1, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
		let expected = "take any of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
		let expected = "take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: 4, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
		let expected = "take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{count: 2, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
		let expected = "take two from among the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(
			&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
		)
		.unwrap();
		let expected = "complete any of the following requirements:

- “A”
- “B”
- “C”
- “D”";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(
			&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
		)
		.unwrap();
		let expected = "complete any of the following requirements:

- “A”
- “B”
- “C”
- “D”";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(
			&"{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
		)
		.unwrap();
		let expected = "complete two from among the following requirements:

- “A”
- “B”
- “C”
- “D”";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(
			&"{count: 2, of: [{both: [CS 111, CS 251]}, {requirement: A}, {requirement: B}, {requirement: C}]}",
		)
		.unwrap();
		let expected = "do two from among the following:

- take both CS 111 and CS 251
- complete the “A” requirement
- complete the “B” requirement
- complete the “C” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
            serde_yaml::from_str(&"{count: any, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}").unwrap();
		let expected = "do any of the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
            serde_yaml::from_str(&"{count: 2, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}").unwrap();
		let expected = "do two from among the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement";
		assert_eq!(expected, input.print().unwrap());
	}
}
