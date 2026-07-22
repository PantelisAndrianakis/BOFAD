// Fixture for the bofad-code-check agent: the corrected twin of SemanticBad.java, expected verdict clean.
public class SemanticGood
{
	public double totalFor(Customer customer)
	{
		double total = 0;
		for (Order order : customer.getOrders())
		{
			final OrderStatus orderStatus = order.getStatus();
			if ((orderStatus == OrderStatus.PAID) && (orderStatus != OrderStatus.REFUNDED))
			{
				total += order.getTotal();
			}
		}

		return Math.round(total * 100.0) / 100.0;
	}

	public String describe(Customer customer)
	{
		final StringBuilder result = new StringBuilder();
		for (Order order : customer.getOrders())
		{
			result.append(order.getId()).append(',');
		}

		return result.toString();
	}

	public String label(int code)
	{
		switch (code)
		{
			case 1:
			{
				return "NEW";
			}
			case 2:
			{
				return "PAID";
			}
			case 3:
			{
				return "SHIPPED";
			}
			default:
			{
				return "UNKNOWN";
			}
		}
	}
}
