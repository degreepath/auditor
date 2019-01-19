mod oxford;
pub use oxford::Oxford;

mod errors;
pub use errors::{ParseError, ValidationError};

mod serde;
pub use self::serde::{serde_false, string_or_struct, string_or_struct_parseerror};

pub fn pretty_term(term: &str) -> String {
	format!("{}", term)
}

pub fn expand_year(year: u64, mode: &str) -> String {
	match mode {
		"short" => format!("{}", year),
		"dual" => {
			let next = year + 1;
			let next = next.to_string();
			let next = &next[2..4];
			format!("{}-{}", year, next)
		}
		_ => panic!("unknown expand_year mode {}", mode),
	}
}

pub fn result_to_option<T, E>(r: Result<T, E>) -> Option<T> {
	match r {
		Ok(v) => Some(v),
		Err(_) => None,
	}
}
