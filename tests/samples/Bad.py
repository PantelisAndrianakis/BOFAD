maxRetries = 3
#Missing space after the marker.


def process_order(order, code):
    # lowercase fragment comment
    status = order.getStatus()
    use(status)
    total = ""
    for item in order.items():
        total += item
    names = map(str, order.items())
    a, b = 1, 2
    value = 1; other = 2
    # The comment wraps at a column instead of
    # at punctuation, and lists x, y, and z.
    use(order.name())
    use(order.name())
    # An em dash — sneaks in here.
    return total   
