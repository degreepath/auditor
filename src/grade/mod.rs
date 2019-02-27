use crate::util::ParseError;
use serde::{Deserialize, Deserializer, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Clone, Eq, Serialize, Deserialize, Hash, PartialOrd, Ord)]
pub enum Grade {
	A,
	Aminus,
	Bplus,
	B,
	Bminus,
	Cplus,
	C,
	Cminus,
	Dplus,
	D,
	Dminus,
	F,
}

impl Grade {
	pub fn numeric(&self) -> [i8; 2] {
		use Grade::*;

		match &self {
			A => [4, 00],
			Aminus => [3, 70],
			Bplus => [3, 30],
			B => [3, 00],
			Bminus => [2, 70],
			Cplus => [2, 30],
			C => [2, 00],
			Cminus => [1, 70],
			Dplus => [1, 30],
			D => [1, 00],
			Dminus => [0, 70],
			F => [0, 00],
		}
	}
}

impl FromStr for Grade {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		use Grade::*;
		let s = s.trim();

		match s {
			"A" => Ok(A),
			"A-" => Ok(Aminus),
			"B+" => Ok(Bplus),
			"B" => Ok(B),
			"B-" => Ok(Bminus),
			"C+" => Ok(Cplus),
			"C" => Ok(C),
			"C-" => Ok(Cminus),
			"D+" => Ok(Dplus),
			"D" => Ok(D),
			"D-" => Ok(Dminus),
			"F" => Ok(F),
			_ => Err(ParseError::InvalidValue),
		}
	}
}

impl fmt::Display for Grade {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		let [major, minor] = self.numeric();
		write!(f, "{}.{}", major, minor)
	}
}

impl From<&Grade> for String {
	fn from(g: &Grade) -> Self {
		use Grade::*;
		match g {
			A => String::from("A"),
			Aminus => String::from("A-"),
			Bplus => String::from("B+"),
			B => String::from("B"),
			Bminus => String::from("B-"),
			Cplus => String::from("C+"),
			C => String::from("C"),
			Cminus => String::from("C-"),
			Dplus => String::from("D+"),
			D => String::from("D"),
			Dminus => String::from("D-"),
			F => String::from("F"),
		}
	}
}

impl From<Grade> for String {
	fn from(g: Grade) -> Self {
		String::from(&g)
	}
}

impl PartialEq<String> for Grade {
	fn eq(&self, rhs: &String) -> bool {
		&String::from(self) == rhs
	}
}

impl PartialEq<Grade> for String {
	fn eq(&self, rhs: &Grade) -> bool {
		rhs == self
	}
}

pub fn option_grade<'de, D>(deserializer: D) -> Result<Option<Grade>, D::Error>
where
	D: Deserializer<'de>,
{
	#[derive(Deserialize)]
	struct Wrapper(#[serde(deserialize_with = "crate::util::string_or_struct_parseerror")] Grade);

	let v = Option::deserialize(deserializer)?;
	Ok(v.map(|Wrapper(a)| a))
}
