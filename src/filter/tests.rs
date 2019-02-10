use super::*;
use crate::traits::print::Print;
use indexmap::indexmap;

#[test]
fn serialize_simple() {
	let data: Clause = indexmap! {
		"level".into() => "100".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Single:
    EqualTo:
      Integer: 100"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn serialize_or() {
	let data: Clause = indexmap! {
		"level".into() => "100 | 200".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Or:
    - EqualTo:
        Integer: 100
    - EqualTo:
        Integer: 200"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);

	let data: Clause = indexmap! {
		"level".into() =>  "< 100 | 200".parse::<WrappedValue>().unwrap(),
	};

	let expected = r#"---
level:
  Or:
    - LessThan:
        Integer: 100
    - EqualTo:
        Integer: 200"#;

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

mod value {
	use super::*;

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
		let expected = Value::Float((1, 0));
		let actual: Value = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "1.5";
		let expected = Value::Float((1, 50));
		let actual: Value = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "1.25";
		let expected = Value::Float((1, 25));
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
}

mod tagged_value {
	use super::*;

	#[test]
	fn deserialize_untagged() {
		let data = "FYW";
		let expected = TaggedValue::EqualTo(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_eq() {
		let data = "= FYW";
		let expected = TaggedValue::EqualTo(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_neq() {
		let data = "! FYW";
		let expected = TaggedValue::NotEqualTo(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_gt() {
		let data = "> FYW";
		let expected = TaggedValue::GreaterThan(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_gte() {
		let data = ">= FYW";
		let expected = TaggedValue::GreaterThanEqualTo(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_lt() {
		let data = "< FYW";
		let expected = TaggedValue::LessThan(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_lte() {
		let data = "<= FYW";
		let expected = TaggedValue::LessThanEqualTo(Value::String("FYW".into()));
		let actual: TaggedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

}

mod wrapped_value {
	use super::*;

	#[test]
	fn deserialize() {
		let data = "FYW";
		let expected = WrappedValue::Single(TaggedValue::EqualTo(Value::String("FYW".into())));
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_ne() {
		let data = "! FYW";
		let expected = WrappedValue::Single(TaggedValue::NotEqualTo(Value::String("FYW".into())));
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_or_ne() {
		let data = "! FYW | = FYW";
		let expected = WrappedValue::Or(vec![
			TaggedValue::NotEqualTo(Value::String("FYW".into())),
			TaggedValue::EqualTo(Value::String("FYW".into())),
		]);
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_or_untagged() {
		let data = "FYW | FYW";
		let expected = WrappedValue::Or(vec![
			TaggedValue::EqualTo(Value::String("FYW".into())),
			TaggedValue::EqualTo(Value::String("FYW".into())),
		]);
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_and_untagged() {
		let data = "FYW & FYW";
		let expected = WrappedValue::And(vec![
			TaggedValue::EqualTo(Value::String("FYW".into())),
			TaggedValue::EqualTo(Value::String("FYW".into())),
		]);
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_and_ne() {
		let data = "! FYW & = FYW";
		let expected = WrappedValue::And(vec![
			TaggedValue::NotEqualTo(Value::String("FYW".into())),
			TaggedValue::EqualTo(Value::String("FYW".into())),
		]);
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_multiword_single_value() {
		let data = "St. Olaf College";
		let expected = WrappedValue::Single(TaggedValue::EqualTo(Value::String("St. Olaf College".into())));
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_negated_multiword_single_value() {
		let data = "! St. Olaf College";
		let expected = WrappedValue::Single(TaggedValue::NotEqualTo(Value::String("St. Olaf College".into())));
		let actual: WrappedValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}
}

fn deserialize_test(s: &str) -> Option<Clause> {
	use serde::Deserialize;
	#[derive(Deserialize)]
	struct Wrapper(#[serde(deserialize_with = "deserialize_with")] Option<Clause>);

	let v: Wrapper = serde_yaml::from_str(s).unwrap();

	v.0
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

	let input: Clause = deserialize_test(&"{credits: '1.0'}").unwrap();
	let expected = "with the “1.0” `credits` attribute";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{credits: '1.5'}").unwrap();
	let expected = "with the “1.50” `credits` attribute";
	assert_eq!(expected, input.print().unwrap());

	let input: Clause = deserialize_test(&"{credits: '1.75'}").unwrap();
	let expected = "with the “1.75” `credits` attribute";
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
