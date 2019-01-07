#[macro_use]
extern crate serde_derive;

extern crate serde;
extern crate serde_yaml;

use std::fmt;
use serde::de::{self, Deserialize, Deserializer, Visitor};

#[derive(Debug)]
struct UserId(u64);

#[derive(Deserialize, Debug)]
struct User {
    id: UserId,
}

impl<'de> Deserialize<'de> for UserId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
        where D: Deserializer<'de>
    {
        struct IdVisitor;

        impl<'de> Visitor<'de> for IdVisitor {
            type Value = UserId;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("user ID as a number or string")
            }

            fn visit_u64<E>(self, id: u64) -> Result<Self::Value, E>
                where E: de::Error
            {
                Ok(UserId(id))
            }

            fn visit_str<E>(self, id: &str) -> Result<Self::Value, E>
                where E: de::Error
            {
                id.parse().map(UserId).map_err(de::Error::custom)
            }
        }

        deserializer.deserialize_any(IdVisitor)
    }
}

fn main() {
    let j = "{\"id\":\"78358783457112\"}";
    println!("{:?}", serde_yaml::from_str::<User>(j).unwrap());
}