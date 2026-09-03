use crate::order::Order;
use std::fs;

const max_retries: i32 = 3;

//Missing space after the marker.
fn process_order(order: &Order) {
    let data = get_data();
	let (a, b) = (0, 0);
	let first: i32 = 1; let second: i32 = 2;
	// lowercase fragment comment
	// The comment wraps at a column instead of
	// at punctuation, and lists x, y, and z.
	let names: Vec<String> = order.items.iter().map(|item| item.name.clone()).collect();
	for item in order.items.iter()
	{
		use_item(item);
	}
	if a > 0 &&
		b > 0
	{
		use_pair(a, b);
	}
	let value: i32 = parse(&data).unwrap();
	// An em dash — sneaks in here.
	use_value(value);   


	use_names(&names);
}

fn wrapped(
	order: &Order,
	code: i32,
) -> i32
{
	code
}
