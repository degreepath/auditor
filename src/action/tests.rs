use super::*;

#[test]
fn count_gte_6() {
	let actual: Action = "count >= 6".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Count.to_string()),
		op: Some(Operator::GreaterThanEqualTo),
		rhs: Some(Value::Integer(6)),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn count_eq_1() {
	let actual: Action = "count = 1".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Count.to_string()),
		op: Some(Operator::EqualTo),
		rhs: Some(Value::Integer(1)),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn average_gte_2_0() {
	let actual: Action = "average >= 2.0".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Average.to_string()),
		op: Some(Operator::GreaterThanEqualTo),
		rhs: Some(Value::Float((2, 0))),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn average_gte_2() {
	let actual: Action = "average >= 2".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Average.to_string()),
		op: Some(Operator::GreaterThanEqualTo),
		rhs: Some(Value::Integer(2)),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn sum_eq_6() {
	let actual: Action = "sum = 6".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Sum.to_string()),
		op: Some(Operator::EqualTo),
		rhs: Some(Value::Integer(6)),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn sum_gte_1_5() {
	let actual: Action = "sum >= 1.5".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Sum.to_string()),
		op: Some(Operator::GreaterThanEqualTo),
		rhs: Some(Value::Float((1, 50))),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn maximum() {
	let actual: Action = "maximum".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Maximum.to_string()),
		op: None,
		rhs: None,
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn minimum() {
	let actual: Action = "minimum".parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(Command::Minimum.to_string()),
		op: None,
		rhs: None,
	};

	assert_eq!(actual, expected_struct);
}

#[test]
fn var_lt_var() {
	let actual: Action = r#""first BTS-T course" < "last EIN course""#.parse().unwrap();

	let expected_struct = Action {
		lhs: Value::String(String::from("first BTS-T course")),
		op: Some(Operator::LessThan),
		rhs: Some(Value::String(String::from("last EIN course"))),
	};

	assert_eq!(actual, expected_struct);
}

#[test]
#[should_panic]
fn invalid_flipped_operator() {
	"a => b".parse::<Action>().unwrap();
}
