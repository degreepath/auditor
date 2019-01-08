// use serde::de::{self, Deserialize, Deserializer, MapAccess, Visitor};
// use serde::ser::{Serialize, SerializeStruct, Serializer};

// should be a superset of GivenRule...
#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct SaveBlock {}

#[cfg(test)]
mod tests {}
