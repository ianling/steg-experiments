from collections.abc import Generator


def generate_default_palette() -> list[tuple[int, int, int]]:
    """generate a list of available colors as tuples in the form: (r, g, b)"""
    # limit RGB values to 16-240 instead of 0-255 to help preserve color
    possible_values = [val for val in range(16, 240, 37)]
    num_possible_values = len(possible_values)

    colors = []
    for r in range(num_possible_values):
        for g in range(num_possible_values):
            for b in possible_values:
                colors.append((possible_values[r], possible_values[g], b))

    # truncate palette down to 255 entries
    colors = colors[0:255]
    # entry 256 is "pure white" (within the 16-240 range)
    colors.append((240, 240, 240))

    return colors


def factors(x) -> Generator[int, None, None]:
    for i in range(2, x//2+1):
        if x % i == 0:
            yield i


def fuzzy_equals(color_a: tuple[int, int, int], color_b: tuple[int, int, int]) -> bool:
    fuzziness = 18  # can be offset by a maximum of this value (37/2 - 1)

    return abs(color_a[0] - color_b[0]) <= fuzziness and abs(color_a[1] - color_b[1]) <= fuzziness and abs(color_a[2] - color_b[2]) <= fuzziness


def list_fuzzy_search(haystack: list[tuple[int, int, int]], needle: tuple[int, int, int]) -> int:
    fuzziness = 18  # can be offset by a maximum of this value

    # check for nulls
    if all([value - fuzziness <= 0 for value in needle]):
        return 0

    for ii, element in enumerate(haystack):
        if fuzzy_equals(element, needle):
            return ii

    raise Exception(f"image was too messed up, couldn't find value for color {needle}")
