from bisect import bisect_left, bisect_right


class BPlusPage:
    def __init__(self, leaf=True):
        self.leaf = leaf
        self.keys = []
        self.values = []
        self.parent = None
        self.next_page = None


class BPlusTree:
    def __init__(self, t=8):
        if t < 2:
            raise ValueError("El grado del B+ debe ser al menos 2")
        self.t = t
        self.root = BPlusPage()
        self.max_claves = 2 * t

    def _find_leaf(self, key):
        page = self.root
        while not page.leaf:
            page = page.values[bisect_right(page.keys, key)]
        return page

    def search(self, key):
        leaf = self._find_leaf(key)
        position = bisect_left(leaf.keys, key)
        if position < len(leaf.keys) and leaf.keys[position] == key:
            return leaf.values[position]
        return None

    def insert(self, key, record):
        leaf = self._find_leaf(key)
        position = bisect_left(leaf.keys, key)
        if position < len(leaf.keys) and leaf.keys[position] == key:
            raise ValueError(f"ID repetido: {key}")
        leaf.keys.insert(position, key)
        leaf.values.insert(position, record)
        if len(leaf.keys) > self.max_claves:
            self._split_leaf(leaf)

    def _split_leaf(self, left_page):
        split_at = len(left_page.keys) // 2
        right_page = BPlusPage()
        right_page.keys = left_page.keys[split_at:]
        right_page.values = left_page.values[split_at:]
        left_page.keys = left_page.keys[:split_at]
        left_page.values = left_page.values[:split_at]
        right_page.next_page = left_page.next_page
        left_page.next_page = right_page
        self._insert_separator(left_page, right_page.keys[0], right_page)

    def _insert_separator(self, left_page, separator, right_page):
        parent = left_page.parent
        if parent is None:
            parent = BPlusPage(leaf=False)
            parent.values = [left_page, right_page]
            parent.keys = [separator]
            left_page.parent = parent
            right_page.parent = parent
            self.root = parent
            return

        position = parent.values.index(left_page)
        parent.keys.insert(position, separator)
        parent.values.insert(position + 1, right_page)
        right_page.parent = parent
        if len(parent.keys) > self.max_claves:
            self._split_internal(parent)

    def _split_internal(self, page):
        midpoint = len(page.keys) // 2
        separator = page.keys[midpoint]
        right_page = BPlusPage(leaf=False)
        right_page.keys = page.keys[midpoint + 1:]
        right_page.values = page.values[midpoint + 1:]
        page.keys = page.keys[:midpoint]
        page.values = page.values[:midpoint + 1]
        for child in right_page.values:
            child.parent = right_page
        self._insert_separator(page, separator, right_page)

    def list_in_order(self):
        leaf = self.root
        while not leaf.leaf:
            leaf = leaf.values[0]
        output_file = []
        while leaf is not None:
            output_file.extend(leaf.values)
            leaf = leaf.next_page
        return output_file

    def search_range(self, minimum, maximum):
        leaf = self._find_leaf(minimum)
        position = bisect_left(leaf.keys, minimum)
        output_file = []
        while leaf is not None:
            for key, record in zip(leaf.keys[position:], leaf.values[position:]):
                if key > maximum:
                    return output_file
                output_file.append(record)
            leaf = leaf.next_page
            position = 0
        return output_file
