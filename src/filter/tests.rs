use super::{CourseClause};
use crate::traits::print::Print;
use crate::value::{SingleValue, TaggedValue, WrappedValue};

#[test]
fn serialize_simple() {
	let data = CourseClause {
		level: Some("100".parse::<WrappedValue<u64>>().unwrap()),
		..CourseClause::default()
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
	let data = CourseClause {
		level: Some("100 | 200".parse::<WrappedValue<u64>>().unwrap()),
		..CourseClause::default()
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

	let data = CourseClause {
		level: Some("< 100 | 200".parse::<WrappedValue<u64>>().unwrap()),
		..CourseClause::default()
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
		let expected = SingleValue::String("FYW".into());
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_value_int() {
		let data = "1";
		let expected = SingleValue::Integer(1);
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "100";
		let expected = SingleValue::Integer(100);
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_value_float() {
		let data = "1.0";
		let expected = SingleValue::Float((1, 0));
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "1.5";
		let expected = SingleValue::Float((1, 50));
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "1.25";
		let expected = SingleValue::Float((1, 25));
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_value_bool() {
		let data = "true";
		let expected = SingleValue::Bool(true);
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);

		let data = "false";
		let expected = SingleValue::Bool(false);
		let actual: SingleValue = data.parse().unwrap();
		assert_eq!(actual, expected);
	}
}

mod tagged_value {
	use super::*;

	#[test]
	fn deserialize_untagged() {
		let data = "FYW";
		let expected = TaggedValue::EqualTo("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_eq() {
		let data = "= FYW";
		let expected = TaggedValue::EqualTo("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_neq() {
		let data = "! FYW";
		let expected = TaggedValue::NotEqualTo("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_gt() {
		let data = "> FYW";
		let expected = TaggedValue::GreaterThan("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_gte() {
		let data = ">= FYW";
		let expected = TaggedValue::GreaterThanEqualTo("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_lt() {
		let data = "< FYW";
		let expected = TaggedValue::LessThan("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_lte() {
		let data = "<= FYW";
		let expected = TaggedValue::LessThanEqualTo("FYW".to_string());
		let actual: TaggedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

}

mod wrapped_value {
	use super::*;

	#[test]
	fn deserialize() {
		let data = "FYW";
		let expected = WrappedValue::Single(TaggedValue::EqualTo("FYW".to_string()));
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_ne() {
		let data = "! FYW";
		let expected = WrappedValue::Single(TaggedValue::NotEqualTo("FYW".to_string()));
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_or_ne() {
		let data = "! FYW | = FYW";
		let expected = WrappedValue::Or(vec![
			TaggedValue::NotEqualTo("FYW".to_string()),
			TaggedValue::EqualTo("FYW".to_string()),
		]);
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_or_untagged() {
		let data = "FYW | FYW";
		let expected = WrappedValue::Or(vec![
			TaggedValue::EqualTo("FYW".to_string()),
			TaggedValue::EqualTo("FYW".to_string()),
		]);
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_and_untagged() {
		let data = "FYW & FYW";
		let expected = WrappedValue::And(vec![
			TaggedValue::EqualTo("FYW".to_string()),
			TaggedValue::EqualTo("FYW".to_string()),
		]);
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_and_ne() {
		let data = "! FYW & = FYW";
		let expected = WrappedValue::And(vec![
			TaggedValue::NotEqualTo("FYW".to_string()),
			TaggedValue::EqualTo("FYW".to_string()),
		]);
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_multiword_single_value() {
		let data = "St. Olaf College";
		let expected = WrappedValue::Single(TaggedValue::EqualTo("St. Olaf College".to_string()));
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_negated_multiword_single_value() {
		let data = "! St. Olaf College";
		let expected = WrappedValue::Single(TaggedValue::NotEqualTo("St. Olaf College".to_string()));
		let actual: WrappedValue<String> = data.parse().unwrap();
		assert_eq!(actual, expected);
	}
}

fn deserialize_test(s: &str) -> CourseClause {
	serde_yaml::from_str(s).unwrap()
}

#[test]
fn pretty_print_single_values() {
	let input = deserialize_test(&"{gereqs: FOL-C}");
	let expected = "with the “FOL-C” general education attribute";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{semester: Interim}");
	let expected = "during Interim semesters";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{semester: Fall}");
	let expected = "during Fall semesters";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{year: '2012'}");
	let expected = "during the 2012-13 academic year";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{institution: 'St. Olaf College'}");
	let expected = "at St. Olaf College";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{department: MATH}");
	let expected = "within the MATH department";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{credits: '1.0'}");
	let expected = "with the “1.00” `credits` attribute";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{credits: '1.5'}");
	let expected = "with the “1.50” `credits` attribute";
	assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{credits: '1.75'}");
	let expected = "with the “1.75” `credits` attribute";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_multiple_values() {
	let input = deserialize_test(&"{semester: Fall | Interim}");
	let expected = "during a Fall or Interim semester";
	assert_eq!(expected, input.print().unwrap());

	// TODO: fix this
	// let input = deserialize_test(&"{year: '2012 | 2013'}");
	// let expected = "during the 2012-13 or 2013-14 academic year";
	// assert_eq!(expected, input.print().unwrap());

	let input = deserialize_test(&"{institution: 'Carleton College | St. Olaf College'}");
	let expected = "at either Carleton College or St. Olaf College";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_negated_value() {
	let input = deserialize_test(&"{department: '! MATH'}");
	let expected = "outside of the MATH department";
	assert_eq!(expected, input.print().unwrap());
}
