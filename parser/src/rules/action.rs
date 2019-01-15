use crate::rules::given::action;
use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
    pub action: action::Action,
}

impl crate::rules::traits::PrettyPrint for Rule {
    fn print(&self) -> Result<String, std::fmt::Error> {
        // use std::fmt::Write;
        // use crate::rules::traits::PrettyPrint;

        let output = String::from("singleton do: rules are as-yet unimplemented");

        // write!(&mut output, "both {} and {}", (*self.both.0).print(), (*self.both.1).print())?;

        Ok(output)
    }
}
