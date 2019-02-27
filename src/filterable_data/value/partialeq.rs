use super::DataValue;

impl PartialEq<bool> for DataValue {
	fn eq(&self, other: &bool) -> bool {
		self.as_bool().map_or(false, |s| s == *other)
	}
}

impl PartialEq<DataValue> for bool {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_bool().map_or(false, |s| s == *self)
	}
}

impl PartialEq<u64> for DataValue {
	fn eq(&self, other: &u64) -> bool {
		self.as_integer().map_or(false, |s| s == *other)
	}
}

impl PartialEq<DataValue> for u64 {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_integer().map_or(false, |s| s == *self)
	}
}

impl PartialEq<u16> for DataValue {
	fn eq(&self, other: &u16) -> bool {
		self.as_integer().map_or(false, |s| s == u64::from(*other))
	}
}

impl PartialEq<DataValue> for u16 {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_integer().map_or(false, |s| s == u64::from(*self))
	}
}

impl PartialEq<(u16, u16)> for DataValue {
	fn eq(&self, other: &(u16, u16)) -> bool {
		self.as_float().map_or(false, |s| s == *other)
	}
}

impl PartialEq<DataValue> for (u16, u16) {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_float().map_or(false, |s| s == *self)
	}
}

impl PartialEq<f32> for DataValue {
	fn eq(&self, other: &f32) -> bool {
		self.as_float().map_or(false, |s| s == DataValue::from(*other))
	}
}

impl PartialEq<DataValue> for f32 {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_float().map_or(false, |s| s == DataValue::from(*self))
	}
}

impl PartialEq<str> for DataValue {
	fn eq(&self, other: &str) -> bool {
		self.as_string().map_or(false, |s| s == other)
	}
}

impl PartialEq<DataValue> for str {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_string().map_or(false, |s| s == self)
	}
}

impl<'a> PartialEq<&'a str> for DataValue {
	fn eq(&self, other: &&str) -> bool {
		self.as_string().map_or(false, |s| s == *other)
	}
}

impl<'a> PartialEq<DataValue> for &'a str {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_string().map_or(false, |s| s == *self)
	}
}

impl PartialEq<String> for DataValue {
	fn eq(&self, other: &String) -> bool {
		self.as_string().map_or(false, |s| s == *other)
	}
}

impl PartialEq<DataValue> for String {
	fn eq(&self, other: &DataValue) -> bool {
		other.as_string().map_or(false, |s| s == *self)
	}
}
