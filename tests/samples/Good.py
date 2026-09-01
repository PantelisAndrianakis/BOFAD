MAX_RETRIES = 3

def processOrder(order: Order, code: int) -> str:
	# The status decides the label, so it is read once and kept.
	orderStatus = order.getStatus()
	if orderStatus == PAID:
		use(orderStatus)
	parts: list = []
	for item in order.items():
		parts.append(item)
	return "".join(parts)
