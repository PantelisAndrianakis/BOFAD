/**
 * Standard class doc comment.<br>
 */
public class Good
{
	/**
	 * Returns the count.<br>
	 * @return the count
	 */
	public int getCount()
	{
		// Timers reset at midnight.
		return 7;
	}

	/**
	 * Guards checker false positives; the var keyword in prose must stay legal.<br>
	 * See https://example.com/checker for background.<br>
	 * @return the guarded count
	 */
	public int getGuardedCount()
	{
		// The var keyword appears only in this comment.
		// See https://example.com/spec for details.
		return 7;
	}
}
