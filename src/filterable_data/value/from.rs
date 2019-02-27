use super::DataValue;
use std::borrow::Cow;
use std::iter::FromIterator;

impl From<bool> for DataValue {
	fn from(f: bool) -> Self {
		DataValue::Boolean(f)
	}
}

impl From<f32> for DataValue {
	fn from(d: f32) -> DataValue {
		DataValue::Float((d.trunc() as u16, (d.fract() * 100.0) as u16))
	}
}

impl<'a> From<&'a str> for DataValue {
	fn from(f: &'a str) -> DataValue {
		DataValue::String(f.to_string())
	}
}

impl From<String> for DataValue {
	fn from(f: String) -> DataValue {
		DataValue::String(f)
	}
}

impl From<u64> for DataValue {
	fn from(n: u64) -> DataValue {
		DataValue::Integer(n)
	}
}

impl<'a> From<Cow<'a, str>> for DataValue {
	fn from(f: Cow<'a, str>) -> Self {
		DataValue::String(f.to_string())
	}
}

impl<T: Into<DataValue>> From<Vec<T>> for DataValue {
	fn from(f: Vec<T>) -> Self {
		DataValue::Vec(f.into_iter().map(Into::into).collect())
	}
}

impl<'a, T: Clone + Into<DataValue>> From<&'a [T]> for DataValue {
	fn from(f: &'a [T]) -> Self {
		DataValue::Vec(f.iter().cloned().map(Into::into).collect())
	}
}

impl<T: Into<DataValue>> FromIterator<T> for DataValue {
	fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
		let vec = iter.into_iter().map(T::into).collect();

		DataValue::Vec(vec)
	}
}

#[cfg(test)]
mod tests {
	use super::DataValue;

	#[test]
	fn from_bool() {
		assert_eq!(DataValue::from(false), DataValue::Boolean(false));
		assert_eq!(DataValue::from(true), DataValue::Boolean(true));
	}

	#[test]
	fn from_str() {
		assert_eq!(DataValue::from("abc"), DataValue::String(String::from("abc")));
	}

	#[test]
	fn from_string() {
		assert_eq!(
			DataValue::from(String::from("abc")),
			DataValue::String(String::from("abc"))
		);
	}

	#[test]
	fn from_float() {
		assert_eq!(DataValue::from(1.0f32), DataValue::Float((1, 0)));
		assert_eq!(DataValue::from(1.5f32), DataValue::Float((1, 50)));
		assert_eq!(DataValue::from(1.25f32), DataValue::Float((1, 25)));
		assert_eq!(DataValue::from(1.025f32), DataValue::Float((1, 2)));
		assert_eq!(DataValue::from(1.0025f32), DataValue::Float((1, 0)));
	}

	#[test]
	fn from_vec() {
		assert_eq!(
			DataValue::from(vec![1, 2, 3]),
			DataValue::Vec(vec![1.into(), 2.into(), 3.into()])
		);
	}
}
