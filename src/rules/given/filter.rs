use serde_yaml::Value as YamlValue;
use std::collections::HashMap;

pub type Value = YamlValue;
pub type Clause = HashMap<String, Value>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize() {
        let mut data = Clause::new();
        data.insert("level".to_string(), 100.into());

        let expected = r#"---
level: 100"#;

        let actual = serde_yaml::to_string(&data).unwrap();

        assert_eq!(actual, expected);
    }
}
