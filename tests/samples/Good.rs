//! Order processing sample in the house style.

use anyhow::{Result, anyhow};

use std::fs;

use crate::order::Order;

const MAX_RETRIES: i32 = 3;

/// Labels every item of an order and returns the labels in order.
pub fn label_items(order: &Order, path: &str) -> Result<Vec<String>>
{
	let bytes: Vec<u8> = fs::read(path).map_err(|e| anyhow!("Failed to read {}: {}", path, e))?;
	let mut labels: Vec<String> = Vec::with_capacity(order.items.len());
	for item in &order.items
	{
		let label: String = match item.priority
		{
			1..=3 => String::from("high"),
			4..=7 => String::from("medium"),
			_ => String::from("low"),
		};
		labels.push(label);
	}

	if bytes.is_empty() && labels.len() > MAX_RETRIES as usize
	{
		return Err(anyhow!("Empty order file {} with {} labels", path, labels.len()));
	}

	Ok(labels)
}

#[cfg(test)]
mod tests
{
	use super::*;

	#[test]
	fn labels_by_priority()
	{
		let order: Order = Order::sample();
		let labels: Vec<String> = label_items(&order, "order.bin").unwrap();
		assert_eq!(labels.len(), order.items.len());
	}
}
