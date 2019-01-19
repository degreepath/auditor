use crate::util::ValidationError;
use std::slice::Iter;

pub trait Validate {
	fn iter_children(&self) -> Iter<crate::rules::Rule>;

	fn validate(&self) -> Result<(), ValidationError> {
		for _child in self.iter_children() {
			// child.validate()?
		}

		Ok(())
	}
}
