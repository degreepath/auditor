use super::*;
use crate::action::Operator;
use crate::traits::print::Print;

#[test]
fn serialize_simple() {
	let data: Clause = btreemap! {
		"level".into() => "100".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Single:
    op: EqualTo
    value:
      Integer: 100"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn serialize_or() {
	let data: Clause = btreemap! {
		"level".into() => "100 | 200".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Or:
    - op: EqualTo
      value:
        Integer: 100
    - op: EqualTo
      value:
        Integer: 200"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);

	let data: Clause = btreemap! {
		"level".into() =>  "< 100 | 200".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Or:
    - op: LessThan
      value:
        Integer: 100
    - op: EqualTo
      value:
        Integer: 200"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_value_str() {
	let data = "FYW";
	let expected = Value::String("FYW".into());
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_value_int() {
	let data = "1";
	let expected = Value::Integer(1);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);

	let data = "100";
	let expected = Value::Integer(100);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_value_float() {
	let data = "1.0";
	let expected = Value::Float(1.0);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);

	let data = "1.5";
	let expected = Value::Float(1.5);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_value_bool() {
	let data = "true";
	let expected = Value::Bool(true);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);

	let data = "false";
	let expected = Value::Bool(false);
	let actual: Value = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_untagged() {
	let data = "FYW";
	let expected = TaggedValue {
		op: Operator::EqualTo,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_eq() {
	let data = "= FYW";
	let expected = TaggedValue {
		op: Operator::EqualTo,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_neq() {
	let data = "! FYW";
	let expected = TaggedValue {
		op: Operator::NotEqualTo,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_gt() {
	let data = "> FYW";
	let expected = TaggedValue {
		op: Operator::GreaterThan,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_gte() {
	let data = ">= FYW";
	let expected = TaggedValue {
		op: Operator::GreaterThanEqualTo,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_lt() {
	let data = "< FYW";
	let expected = TaggedValue {
		op: Operator::LessThan,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_tagged_value_lte() {
	let data = "<= FYW";
	let expected = TaggedValue {
		op: Operator::LessThanEqualTo,
		value: Value::String("FYW".into()),
	};
	let actual: TaggedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value() {
	let data = "FYW";
	let expected = WrappedValue::Single(TaggedValue {
		op: Operator::EqualTo,
		value: Value::String("FYW".into()),
	});
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value_ne() {
	let data = "! FYW";
	let expected = WrappedValue::Single(TaggedValue {
		op: Operator::NotEqualTo,
		value: Value::String("FYW".into()),
	});
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value_or_ne() {
	let data = "! FYW | = FYW";
	let expected = WrappedValue::Or(vec![
		TaggedValue {
			op: Operator::NotEqualTo,
			value: Value::String("FYW".into()),
		},
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
	]);
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value_or_untagged() {
	let data = "FYW | FYW";
	let expected = WrappedValue::Or(vec![
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
	]);
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value_and_untagged() {
	let data = "FYW & FYW";
	let expected = WrappedValue::And(vec![
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
	]);
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_wrapped_value_and_ne() {
	let data = "! FYW & = FYW";
	let expected = WrappedValue::And(vec![
		TaggedValue {
			op: Operator::NotEqualTo,
			value: Value::String("FYW".into()),
		},
		TaggedValue {
			op: Operator::EqualTo,
			value: Value::String("FYW".into()),
		},
	]);
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

fn deserialize_test(s: &str) -> Option<Clause> {
	#[derive(Deserialize)]
	struct Wrapper(#[serde(deserialize_with = "deserialize_with")] Option<Clause>);

	let v: Wrapper = serde_yaml::from_str(s).unwrap();

	v.0
}

#[test]
fn deserialize_wrapped_value_multiword_single_value() {
	let data = "St. Olaf College";
	let expected = WrappedValue::Single(TaggedValue {
		op: Operator::EqualTo,
		value: Value::String("St. Olaf College".into()),
	});
	let actual: WrappedValue = data.parse().unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn pretty_print_single_values() {
	let input: Clause = deserialize_test(&"{gereqs: FOL-C}").unwrap();
	let expected = "with the “FOL-C” general education attribute";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{semester: Interim}").unwrap();
	let expected = "during Interim semesters";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{semester: Fall}").unwrap();
	let expected = "during Fall semesters";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{year: '2012'}").unwrap();
	let expected = "during the 2012-13 academic year";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{institution: 'St. Olaf College'}").unwrap();
	let expected = "at St. Olaf College";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{department: MATH}").unwrap();
	let expected = "within the MATH department";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_multiple_values() {
	let input: Clause = deserialize_test(&"{semester: Fall | Interim}").unwrap();
	let expected = "during a Fall or Interim semester";
	assert_eq!(expected, input.print().unwrap());

	// TODO: fix this
	// let input: Clause = deserialize_test(&"{year: '2012 | 2013'}").unwrap();
	// let expected = "during the 2012-13 or 2013-14 academic year";
	// assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{institution: 'Carleton College | St. Olaf College'}").unwrap();
	let expected = "at either Carleton College or St. Olaf College";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_negated_value() {
	let input: Clause = deserialize_test(&"{department: '! MATH'}").unwrap();
	let expected = "outside of the MATH department";
	assert_eq!(expected, input.print().unwrap());
}
