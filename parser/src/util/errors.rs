use std::error::Error;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
	InvalidAction,
	UnknownOperator,
	InvalidValue,
	UnknownCommand,
	InvalidVariableName,
}

impl fmt::Display for ParseError {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_str(self.description())
	}
}

impl Error for ParseError {
	fn description(&self) -> &str {
		"invalid do: command syntax"
	}
}
