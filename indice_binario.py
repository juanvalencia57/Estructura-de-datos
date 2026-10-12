class SearchNode:
    def __init__(self, record):
        self.record = record
        self.key = record["id"]
        self.left = None
        self.right = None


class ABBTree:
    def __init__(self):
        self.root = None

    def insert(self, record):
        new_node = SearchNode(record)
        if self.root is None:
            self.root = new_node
            return

        current = self.root
        while True:
            if new_node.key == current.key:
                raise ValueError(f"ID repetido: {new_node.key}")
            if new_node.key < current.key:
                if current.left is None:
                    current.left = new_node
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = new_node
                    return
                current = current.right

    def search(self, key):
        current = self.root
        while current is not None:
            if key == current.key:
                return current.record
            current = current.left if key < current.key else current.right
        return None

    def list_in_order(self):
        result = []
        pending = []
        current = self.root
        while pending or current is not None:
            while current is not None:
                pending.append(current)
                current = current.left
            current = pending.pop()
            result.append(current.record)
            current = current.right
        return result

    def search_range(self, minimum, maximum):
        matches = []
        pila = []
        current = self.root
        while pila or current is not None:
            while current is not None:
                pila.append(current)
                current = current.left
            current = pila.pop()
            if current.key > maximum:
                break
            if current.key >= minimum:
                matches.append(current.record)
            current = current.right
        return matches
