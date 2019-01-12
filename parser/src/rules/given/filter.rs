use serde_yaml::Value as YamlValue;
use std::collections::HashMap;

pub type Clause = HashMap<String, Value>;
pub type Value = YamlValue;

pub enum V {
    String(String),
    Integer(u64),
    Float(f64),
    Vec(Vec<V>),
}

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
