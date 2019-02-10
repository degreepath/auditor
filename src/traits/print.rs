use std::fmt;

pub type Result = std::result::Result<String, fmt::Error>;

pub trait Print {
	fn print(&self) -> Result;

	fn print_indented(&self, level: usize) -> Result {
		let printed = self.print()?;

		if printed.contains('\n') {
			Ok(indent_non_empty_lines(&printed, level))
		} else {
			Ok(printed.to_string())
		}
	}
}

fn indent_non_empty_lines(s: &str, times: usize) -> String {
	let lines: Vec<_> = s.lines().collect();

	if let Some((first, rest)) = lines.split_first() {
		let indent = "    ".repeat(times);

		// don't indent empty lines
		let rest = rest.iter().map(|l| {
			if l.trim() != "" {
				format!("{}{}", indent, l)
			} else {
				String::from("")
			}
		});

		// skip the first blank line
		let rest = rest.skip_while(|l| l.is_empty());

		let rest = rest.collect::<Vec<_>>().join("\n");

		format!("{}\n{}", first, rest)
	} else {
		s.to_string()
	}
}
