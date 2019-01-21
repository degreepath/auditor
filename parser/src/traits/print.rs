use std::fmt;

pub type Result = std::result::Result<String, fmt::Error>;

pub trait Print {
	fn print(&self) -> Result;

	fn print_indented(&self, level: usize) -> Result {
		let printed = self.print()?;

		if printed.contains("\n") {
			let lines = printed.lines().collect::<Vec<_>>();
			if let Some((first, rest)) = lines.split_first() {
				let indent = "    ".repeat(level);

				let rest = rest
					.iter()
					// don't indent empty lines
					.map(|l| if l.trim() != "" {
						format!("{}{}", indent, l)
					} else {
						String::from("")
					})
					// skip the first blank line
					.skip_while(|l| l == "")
					.collect::<Vec<_>>()
					.join("\n");

				Ok(format!("{}\n{}", first, rest))
			} else {
				Ok(printed.to_string())
			}
		} else {
			Ok(printed.to_string())
		}
	}
}
