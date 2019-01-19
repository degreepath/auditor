pub trait Oxford {
	fn oxford(&self, trailer: &str) -> String;
}

impl Oxford for Vec<String> {
	fn oxford(&self, trailer: &str) -> String {
		if self.len() == 1 {
			return format!("{}", self[0]);
		}

		if self.len() == 2 {
			return format!("{} {} {}", self[0], trailer, self[1]);
		}

		if let Some((last, rest)) = self.split_last() {
			return format!("{}, {} {}", rest.join(", "), trailer, last);
		}

		String::new()
	}
}

#[cfg(test)]
mod tests {
	#[test]
	fn oxford_len_eq0() {
		use super::Oxford;
		assert_eq!("", vec![].oxford("and"));
	}

	#[test]
	fn oxford_len_eq1() {
		use super::Oxford;
		assert_eq!("A", vec!["A".to_string()].oxford("and"));
	}

	#[test]
	fn oxford_len_eq2() {
		use super::Oxford;
		assert_eq!("A and B", vec!["A".to_string(), "B".to_string()].oxford("and"));
		assert_eq!("A or B", vec!["A".to_string(), "B".to_string()].oxford("or"));
	}

	#[test]
	fn oxford_len_gt3() {
		use super::Oxford;
		assert_eq!(
			"A, B, and C",
			vec!["A".to_string(), "B".to_string(), "C".to_string()].oxford("and")
		);
		assert_eq!(
			"A, B, or C",
			vec!["A".to_string(), "B".to_string(), "C".to_string()].oxford("or")
		);
	}
}
