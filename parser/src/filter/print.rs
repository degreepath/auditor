use super::Clause;
use super::{TaggedValue, Value, WrappedValue};
use crate::action::Operator;
use crate::traits::print;
use crate::util::{self, Oxford};

impl print::Print for Clause {
	fn print(&self) -> print::Result {
		let mut clauses = vec![];
		let mut expected_count = self.len();

		let mut used_keys = std::collections::HashSet::new();

		if let Some(gereq) = self.get("gereqs") {
			used_keys.insert("gereqs".to_string());
			match gereq {
				WrappedValue::Single(v) => {
					clauses.push(format!("with the “{}” general education attribute", v.print()?))
				}
				WrappedValue::Or(_) | WrappedValue::And(_) => {
					// TODO: figure out how to quote these
					clauses.push(format!("with the {} general education attribute", gereq.print()?));
				}
			};
		}

		if let Some(semester) = self.get("semester") {
			used_keys.insert("semester".to_string());
			match semester {
				WrappedValue::Single(v) => clauses.push(format!("during {} semesters", v.print()?)),
				WrappedValue::Or(_) | WrappedValue::And(_) => {
					clauses.push(format!("during a {} semester", semester.print()?))
				}
			};
		}

		if let Some(year) = self.get("year") {
			used_keys.insert("year".to_string());
			match year {
				WrappedValue::Single(TaggedValue {
					op: Operator::EqualTo,
					value: Value::Integer(n),
				}) => clauses.push(format!("during the {} academic year", util::expand_year(*n, "dual"))),
				WrappedValue::Or(_) | WrappedValue::And(_) => {
					// TODO: implement a .map() function on WrappedValue?
					// to allow something like `year.map(util::expand_year).print()?`
					clauses.push(format!("during the {} academic years", year.print()?));
				}
				_ => unimplemented!("filter:year, WrappedValue::Single, not using = [0-9] {:?}", year),
			}
		}

		if let Some(institution) = self.get("institution") {
			used_keys.insert("institution".to_string());
			match institution {
				WrappedValue::Single(v) => clauses.push(format!("at {}", v.print()?)),
				WrappedValue::Or(_) => {
					clauses.push(format!("at either {}", institution.print()?));
				}
				WrappedValue::And(_) => unimplemented!("filter:institution, and-value"),
			}
		}

		match (self.get("department"), self.get("number"), self.get("section")) {
			(Some(department), None, None) => {
				used_keys.insert("department".to_string());

				match department {
					WrappedValue::Single(TaggedValue {
						op: Operator::EqualTo,
						value: v,
					}) => clauses.push(format!("within the {} department", v.print()?)),
					WrappedValue::Single(TaggedValue {
						op: Operator::NotEqualTo,
						value: v,
					}) => clauses.push(format!("outside of the {} department", v.print()?)),
					WrappedValue::Single(TaggedValue { op: _, value: _ }) => {
						unimplemented!("filter:department, only implemented for = and !=")
					}
					WrappedValue::Or(v) => match v.len() {
						2 => clauses.push(format!("within either of the {} departments", department.print()?)),
						_ => clauses.push(format!("within the {} department", department.print()?)),
					},
					WrappedValue::And(_) => unimplemented!("filter:dept, and-value"),
				}
			}
			(Some(department), Some(number), None) => {
				used_keys.insert("department".to_string());
				used_keys.insert("number".to_string());
				expected_count -= 1;

				match (department, number) {
					(
						WrappedValue::Single(TaggedValue {
							op: Operator::EqualTo,
							value: department,
						}),
						WrappedValue::Single(TaggedValue {
							op: Operator::EqualTo,
							value: number,
						}),
					) => clauses.push(format!("called {} {} [todo]", department.print()?, number.print()?)),
					(
						WrappedValue::Single(TaggedValue {
							op: Operator::EqualTo,
							value: department,
						}),
						WrappedValue::Single(TaggedValue {
							op: Operator::NotEqualTo,
							value: number,
						}),
					) => clauses.push(format!("other than {} {}", department.print()?, number.print()?)),
					(
						WrappedValue::Or(v),
						WrappedValue::Single(TaggedValue {
							op: Operator::GreaterThanEqualTo,
							value: n,
						}),
					) => match v.len() {
						2 => clauses.push(format!(
							"within either of the {} departments, past {}",
							department.print()?,
							n.print()?
						)),
						_ => clauses.push(format!(
							"within the {} department past {}",
							department.print()?,
							n.print()?
						)),
					},
					_ => unimplemented!("filter:dept+num, certain modes"),
				}
			}
			(None, Some(number), None) => {
				used_keys.insert("number".to_string());

				match number {
					WrappedValue::Single(TaggedValue {
						op: Operator::EqualTo,
						value: v,
					}) => clauses.push(format!("numbered {}", v.print()?)),
					WrappedValue::Single(TaggedValue {
						op: Operator::NotEqualTo,
						value: v,
					}) => clauses.push(format!("not numbered {}", v.print()?)),
					_ => unimplemented!("filter:num, certain modes"),
				}
			}
			(Some(_), Some(_), Some(_)) => unimplemented!("filter:department+section"),
			(Some(_), None, Some(_)) => unimplemented!("filter:department+section"),
			(None, Some(_), Some(_)) => unimplemented!("filter:number+section"),
			(None, None, Some(_)) => unimplemented!("filter:section"),
			(None, None, None) => (),
		}

		if let Some(level) = self.get("level") {
			used_keys.insert("level".to_string());
			match level {
				WrappedValue::Single(TaggedValue {
					op: Operator::GreaterThanEqualTo,
					value: v,
				}) => clauses.push(format!("at or above the {} level", v.print()?)),
				WrappedValue::Single(v) => clauses.push(format!("at the {} level", v.print()?)),
				WrappedValue::Or(_) => {
					clauses.push(format!("at either the {} level", level.print()?));
				}
				WrappedValue::And(_) => unimplemented!("filter:level, and-value"),
			}
		}

		if let Some(graded) = self.get("graded") {
			used_keys.insert("graded".to_string());
			match graded {
				WrappedValue::Single(TaggedValue {
					op: Operator::NotEqualTo,
					value: Value::Bool(false),
				})
				| WrappedValue::Single(TaggedValue {
					op: Operator::EqualTo,
					value: Value::Bool(true),
				}) => clauses.push(format!("as \"graded\" courses")),
				WrappedValue::Single(TaggedValue {
					op: Operator::NotEqualTo,
					value: Value::Bool(true),
				})
				| WrappedValue::Single(TaggedValue {
					op: Operator::EqualTo,
					value: Value::Bool(false),
				}) => clauses.push(format!("as _not_ \"graded\" courses")),
				_ => unimplemented!("filter:graded, {:?}", graded),
			}
		}

		match (self.get("type"), self.get("name")) {
			(Some(kind), Some(major)) if *kind == WrappedValue::new("major") => {
				used_keys.insert("type".to_string());
				used_keys.insert("name".to_string());
				expected_count -= 1;

				match major {
					WrappedValue::Single(v) => clauses.push(format!("“{}” major", v.print()?)),
					WrappedValue::Or(_) => {
						clauses.push(format!("either a {} major", major.print()?));
					}
					WrappedValue::And(_) => unimplemented!("filter:type=major+name, and-value"),
				}
			}
			(Some(kind), None) if *kind == WrappedValue::new("major") => {
				used_keys.insert("type".to_string());
				match kind {
					WrappedValue::Single(_) => clauses.push("major".to_string()),
					WrappedValue::Or(_) => {
						clauses.push(format!("either {}", kind.print()?));
					}
					WrappedValue::And(_) => unimplemented!("filter:type=major, and-value"),
				}
			}
			(Some(kind), None) => {
				used_keys.insert("type".to_string());
				match kind {
					WrappedValue::Single(v) => clauses.push(format!("“{}”", v.print()?)),
					WrappedValue::Or(_) => {
						clauses.push(format!("either {}", kind.print()?));
					}
					WrappedValue::And(_) => unimplemented!("filter:type, and-value"),
				}
			}
			(None, None) => (),
			_ => unimplemented!("certain combinations of type+major keys in a filter, like {:?}", &self),
		}

		for key in self.keys() {
			if used_keys.contains(key) {
				continue;
			}

			if let Some(value) = self.get(key) {
				match value {
					WrappedValue::Single(v) => {
						clauses.push(format!("with the “{}” `{}` attribute", v.print()?, key))
					}
					WrappedValue::Or(_) => {
						clauses.push(format!("with either the {} `{}` attribute", value.print()?, key))
					}
					WrappedValue::And(_) => {
						clauses.push(format!("with both the {} `{}` attribute", value.print()?, key));
					}
				}
			}
		}

		assert!(
			clauses.len() == expected_count,
			"not all keys from {:?} were used in {:?} (expected: {}, used: {})",
			self,
			clauses,
			expected_count,
			clauses.len()
		);

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}
