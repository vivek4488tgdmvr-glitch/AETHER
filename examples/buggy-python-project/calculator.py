def average(values):
    # Intentional bug: integer division loses precision in Python 2-style code.
    total = sum(values)
    return total // len(values)


def normalize_name(name):
    # Intentional bug: None input crashes without a useful validation message.
    return name.strip().title()


def is_even(number):
    return number % 2 == 1
