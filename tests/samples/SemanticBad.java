// Fixture for the bofad-code-check agent: mechanically clean, semantically dirty.
// Planted violations: uncached repeated getter, single-use local, string concatenation in a loop, if/else chain on the same variable with four branches.
public class SemanticBad
{
	public double totalFor(Customer customer)
	{
		double total = 0;
		for (Order order : customer.getOrders())
		{
			if ((order.getStatus() == OrderStatus.PAID) && (order.getStatus() != OrderStatus.REFUNDED))
			{
				total += order.getTotal();
			}
		}

		final double rounded = Math.round(total * 100.0) / 100.0;
		return rounded;
	}

	public String describe(Customer customer)
	{
		String result = "";
		for (Order order : customer.getOrders())
		{
			result += order.getId() + ",";
		}

		return result;
	}

	public String label(int code)
	{
		if (code == 1)
		{
			return "NEW";
		}
		else if (code == 2)
		{
			return "PAID";
		}
		else if (code == 3)
		{
			return "SHIPPED";
		}
		else
		{
			return "UNKNOWN";
		}
	}
}
