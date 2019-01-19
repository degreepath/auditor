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

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidationError {
	GivenAreasMustOutputAreas,
}

impl fmt::Display for ValidationError {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_str(self.description())
	}
}

impl Error for ValidationError {
	fn description(&self) -> &str {
		match &self {
			ValidationError::GivenAreasMustOutputAreas => {
				"in a `given: areas of study` block, `what:` must also be `areas of study`"
			}
		}
	}
}
