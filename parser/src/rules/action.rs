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

#[cfg(test)]
mod test {
		use super::*;

		#[test]
    #[ignore]
    fn pretty_print_block() {
        use crate::rules::traits::PrettyPrint;

        let input: Rule = serde_yaml::from_str(
            &"---
given: these courses
courses: [DANCE 399]
where: {year: graduation-year, semester: Fall}
name: $dance_seminars
label: Senior Dance Seminars
",
        )
        .unwrap();
        let expected = "Given the intersection between the following potential courses and your transcript, but limiting your transcript to only the courses taken in the Fall of your Senior year, as “Senior Dance Seminars”:

| Potential | “Senior Dance Seminars” |
| --------- | ----------------------- |
| DANCE 399 | DANCE 399 2015-1        |";
        assert_eq!(expected, input.print().unwrap());
    }
}
