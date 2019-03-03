use crate::util::ParseError;
use serde::{Deserialize, Deserializer, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Clone, Eq, Serialize, Deserialize, Hash, PartialOrd, Ord)]
pub enum Grade {
	#[serde(rename = "A+")]
	Aplus,
	A,
	#[serde(rename = "A-")]
	Aminus,
	#[serde(rename = "B+")]
	Bplus,
	B,
	#[serde(rename = "B-")]
	Bminus,
	#[serde(rename = "C+")]
	Cplus,
	C,
	#[serde(rename = "C-")]
	Cminus,
	#[serde(rename = "D+")]
	Dplus,
	D,
	#[serde(rename = "D-")]
	Dminus,
	F,
}

impl Grade {
	pub fn numeric(&self) -> [i8; 2] {
		use Grade::*;

		match &self {
			Aplus => [4, 30],
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
			"A+" => Ok(Aplus),
			"4.3" => Ok(Aplus),
			"4.30" => Ok(Aplus),
			"A" => Ok(A),
			"4.0" => Ok(Aminus),
			"4.00" => Ok(Aminus),
			"A-" => Ok(Aminus),
			"3.7" => Ok(Aminus),
			"3.70" => Ok(Aminus),
			"B+" => Ok(Bplus),
			"3.3" => Ok(Bplus),
			"3.30" => Ok(Bplus),
			"B" => Ok(B),
			"3.0" => Ok(B),
			"3.00" => Ok(B),
			"B-" => Ok(Bminus),
			"2.7" => Ok(Bminus),
			"2.70" => Ok(Bminus),
			"C+" => Ok(Cplus),
			"2.3" => Ok(Cplus),
			"2.30" => Ok(Cplus),
			"C" => Ok(C),
			"2.0" => Ok(C),
			"2.00" => Ok(C),
			"C-" => Ok(Cminus),
			"1.7" => Ok(Cminus),
			"1.70" => Ok(Cminus),
			"D+" => Ok(Dplus),
			"1.3" => Ok(Dplus),
			"1.30" => Ok(Dplus),
			"D" => Ok(D),
			"1.0" => Ok(D),
			"1.00" => Ok(D),
			"D-" => Ok(Dminus),
			"0.7" => Ok(Dminus),
			"0.70" => Ok(Dminus),
			"F" => Ok(F),
			"0.0" => Ok(F),
			"0.00" => Ok(F),
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
			Aplus => String::from("A+"),
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
