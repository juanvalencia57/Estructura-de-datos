# Árbol de Merkle con SHA-256
# Basado en el código de Pranay Arora (TSEC-2023), extendido con:
#   - punteros a nodo padre (para poder generar pruebas de inclusión)
#   - generación de pruebas de inclusión (Merkle proof) para un bloque
#   - verificación de pruebas de inclusión
#   - experimento completo pedido: 5 bloques, raíz, modificación de un
#     bloque, prueba del bloque 3 y verificación con dato incorrecto.

from typing import List, Optional, Tuple, Dict
import hashlib

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    _MATPLOTLIB_DISPONIBLE = True
except ImportError:
    _MATPLOTLIB_DISPONIBLE = False


class Node:
    def __init__(self, left, right, value: str, content, is_copied: bool = False) -> None:
        self.left: Optional["Node"] = left
        self.right: Optional["Node"] = right
        self.parent: Optional["Node"] = None   # <-- necesario para las pruebas
        self.value = value
        self.content = content
        self.is_copied = is_copied

    @staticmethod
    def hash(val: str) -> str:
        return hashlib.sha256(val.encode('utf-8')).hexdigest()

    def __str__(self):
        return (str(self.value))

    def copy(self):
        """
        class copy function
        """
        return Node(self.left, self.right, self.value, self.content, True)


class MerkleTree:
    def __init__(self, values: List[str]) -> None:
        self.__buildTree(values)

    def __buildTree(self, values: List[str]) -> None:
        leaves: List[Node] = [Node(None, None, Node.hash(e), e)
                               for e in values]

        if len(leaves) % 2 == 1:
            # duplicate last elem if odd number of elements
            leaves.append(leaves[-1].copy())

        # guardamos la referencia a las hojas para poder ubicar cualquier
        # bloque original por índice cuando generemos una prueba
        self.leaves: List[Node] = leaves
        self.root: Node = self.__buildTreeRec(leaves)

    def __buildTreeRec(self, nodes: List[Node]) -> Node:
        if len(nodes) % 2 == 1:
            # duplicate last elem if odd number of elements
            nodes.append(nodes[-1].copy())
        half: int = len(nodes) // 2

        if len(nodes) == 2:
            parent = Node(nodes[0], nodes[1],
                          Node.hash(nodes[0].value + nodes[1].value),
                          nodes[0].content + "+" + nodes[1].content)
            nodes[0].parent = parent
            nodes[1].parent = parent
            return parent

        left: Node = self.__buildTreeRec(nodes[:half])
        right: Node = self.__buildTreeRec(nodes[half:])
        value: str = Node.hash(left.value + right.value)
        content: str = f'{left.content}+{right.content}'
        parent = Node(left, right, value, content)
        left.parent = parent
        right.parent = parent
        return parent

    def printTree(self) -> None:
        self.__printTreeRec(self.root)

    def __printTreeRec(self, node: Node) -> None:
        if node != None:
            if node.left != None:
                print("Left: " + str(node.left))
                print("Right: " + str(node.right))
            else:
                print("Input")

            if node.is_copied:
                print('(Padding)')
            print("Value: " + str(node.value))
            print("Content: " + str(node.content))
            print("")
            self.__printTreeRec(node.left)
            self.__printTreeRec(node.right)

    def getRootHash(self) -> str:
        return self.root.value

    # ------------------------------------------------------------------
    # Prueba de inclusión (Merkle proof)
    # ------------------------------------------------------------------
    def getProof(self, index: int) -> List[Tuple[str, str]]:
        """
        Genera la prueba de inclusión para el bloque original ubicado en
        `index` (0-indexado, sobre la lista de `values` original).

        Devuelve una lista de tuplas (hash_hermano, posicion), recorriendo
        el árbol desde la hoja hasta la raíz usando los punteros `parent`.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Indice de bloque fuera de rango")

        node = self.leaves[index]
        proof: List[Tuple[str, str]] = []

        while node.parent is not None:
            parent = node.parent
            if parent.left is node:
                sibling = parent.right
                position = "right"
            else:
                sibling = parent.left
                position = "left"
            proof.append((sibling.value, position))
            node = parent

        return proof

    @staticmethod
    def verifyProof(content: str, proof: List[Tuple[str, str]], root_hash: str) -> bool:
        """
        Verifica que `content` (el dato original del bloque) pertenece al
        árbol cuya raíz es `root_hash`, usando la prueba `proof` generada
        por getProof().
        """
        computed = Node.hash(content)
        for sibling_value, position in proof:
            if position == "right":
                computed = Node.hash(computed + sibling_value)
            else:
                computed = Node.hash(sibling_value + computed)
        return computed == root_hash


# ======================================================================
# VISUALIZACION DEL ARBOL
# ======================================================================
def _asignar_posiciones(node: Node, profundidad: int, contador: List[int],
                         posiciones: Dict[Node, Tuple[float, int]]) -> float:
    """
    Recorre el arbol y asigna a cada nodo una posicion (x, y):
    - x: posicion horizontal, calculada en orden (las hojas se numeran
      de izquierda a derecha y los nodos internos quedan centrados
      sobre sus hijos).
    - y: -profundidad, para que la raiz quede arriba (y=0) y las hojas
      abajo (y negativo).
    """
    if node.left is None and node.right is None:
        x = float(contador[0])
        contador[0] += 1
        posiciones[node] = (x, -profundidad)
        return x

    x_izq = _asignar_posiciones(node.left, profundidad + 1, contador, posiciones)
    x_der = _asignar_posiciones(node.right, profundidad + 1, contador, posiciones)
    x = (x_izq + x_der) / 2
    posiciones[node] = (x, -profundidad)
    return x


def visualizar_arbol(tree: MerkleTree, proof_index: Optional[int] = None,
                      filename: str = "merkle_tree.png") -> None:
    """
    Dibuja el arbol de Merkle completo con matplotlib y lo guarda como PNG.

    Si se pasa `proof_index`, resalta en verde el camino de la prueba de
    inclusion para ese bloque (la hoja, los hermanos usados en la prueba
    y la raiz).

    Si matplotlib no esta instalado, no lanza un error; solo avisa por
    consola y continua sin generar el grafico.
    """
    if not _MATPLOTLIB_DISPONIBLE:
        print("  [Aviso] matplotlib no esta instalado: se omite el grafico.")
        print("  Para verlo, ejecuta: pip install matplotlib")
        return

    posiciones: Dict[Node, Tuple[float, int]] = {}
    _asignar_posiciones(tree.root, 0, [0], posiciones)

    # Nodos que forman parte del camino de la prueba (para resaltarlos)
    camino_prueba: set = set()
    if proof_index is not None:
        nodo = tree.leaves[proof_index]
        camino_prueba.add(nodo)
        while nodo.parent is not None:
            parent = nodo.parent
            hermano = parent.right if parent.left is nodo else parent.left
            camino_prueba.add(hermano)
            camino_prueba.add(parent)
            nodo = parent

    fig, ax = plt.subplots(figsize=(14, 8))

    # --- dibujar las aristas (padre -> hijo) ---
    def dibujar_aristas(node: Node) -> None:
        x0, y0 = posiciones[node]
        for hijo in (node.left, node.right):
            if hijo is not None:
                x1, y1 = posiciones[hijo]
                en_camino = node in camino_prueba and hijo in camino_prueba
                ax.plot([x0, x1], [y0, y1],
                        color="#2ecc71" if en_camino else "#b0b0b0",
                        linewidth=2.5 if en_camino else 1.2, zorder=1)
                dibujar_aristas(hijo)

    dibujar_aristas(tree.root)

    # --- dibujar los nodos ---
    for node, (x, y) in posiciones.items():
        es_hoja = node.left is None and node.right is None
        es_raiz = node is tree.root
        en_camino = node in camino_prueba

        if es_raiz:
            color = "#f1c40f"       # amarillo para la raiz
        elif node.is_copied:
            color = "#e0e0e0"       # gris para nodos de padding
        elif es_hoja:
            color = "#5dade2"       # azul para hojas reales
        else:
            color = "#aed6f1"       # azul claro para nodos internos

        borde = "#27ae60" if en_camino else "#34495e"
        grosor_borde = 2.5 if en_camino else 1.0

        ancho, alto = 0.9, 0.55
        rect = mpatches.FancyBboxPatch((x - ancho / 2, y - alto / 2), ancho, alto,
                                        boxstyle="round,pad=0.02",
                                        linewidth=grosor_borde,
                                        edgecolor=borde, facecolor=color, zorder=2)
        ax.add_patch(rect)

        etiqueta = node.value[:8] + "..."
        if node.is_copied:
            etiqueta += "\n(padding)"
        ax.text(x, y, etiqueta, ha="center", va="center", fontsize=8, zorder=3)

    # --- etiquetas de las hojas con el contenido original ---
    for i, leaf in enumerate(tree.leaves):
        x, y = posiciones[leaf]
        contenido = leaf.content if not leaf.is_copied else f"(copia de bloque {i-1})"
        ax.text(x, y - 0.55, contenido[:22], ha="center", va="top",
                fontsize=7, color="#555555", rotation=0)

    # --- leyenda ---
    leyenda = [
        mpatches.Patch(color="#f1c40f", label="Raiz (Merkle Root)"),
        mpatches.Patch(color="#5dade2", label="Hoja (bloque real)"),
        mpatches.Patch(color="#e0e0e0", label="Hoja de padding (duplicada)"),
        mpatches.Patch(color="#aed6f1", label="Nodo interno"),
    ]
    if proof_index is not None:
        leyenda.append(mpatches.Patch(facecolor="white", edgecolor="#27ae60",
                                       linewidth=2.5, label=f"Camino de la prueba (bloque {proof_index})"))
    ax.legend(handles=leyenda, loc="lower center", bbox_to_anchor=(0.5, -0.15),
              ncol=3, fontsize=8, frameon=False)

    ax.set_title("Arbol de Merkle (SHA-256)", fontsize=13, fontweight="bold")
    ax.set_xlim(-1, max(x for x, _ in posiciones.values()) + 1)
    ax.set_ylim(min(y for _, y in posiciones.values()) - 1.3, 1)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Grafico guardado en: {filename}")


# ======================================================================
# EXPERIMENTO
# ======================================================================
def separador(titulo: str) -> None:
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


def experimento_merkle() -> None:
    # ------------------------------------------------------------------
    # 1) Crear 5 bloques de datos (transacciones simuladas)
    # ------------------------------------------------------------------
    separador("1) Bloques de datos originales (transacciones simuladas)")
    transacciones = [
        "TX1: Ana envia 10 BTC a Beto",
        "TX2: Beto envia 3 BTC a Carla",
        "TX3: Carla envia 7 BTC a David",
        "TX4: David envia 1 BTC a Elena",
        "TX5: Elena envia 5 BTC a Ana",
    ]
    for i, tx in enumerate(transacciones):
        print(f"  Bloque {i}: {tx}")

    # ------------------------------------------------------------------
    # 2) Construir el árbol y mostrar la raíz
    # ------------------------------------------------------------------
    separador("2) Construccion del arbol y Merkle Root")
    tree = MerkleTree(transacciones)
    print(f"  Merkle Root: {tree.getRootHash()}")
    visualizar_arbol(tree, filename="merkle_tree.png")

    # ------------------------------------------------------------------
    # 3) Modificar un bloque y demostrar que la raíz cambia
    # ------------------------------------------------------------------
    separador("3) Modificacion de un bloque -> la raiz cambia")
    root_original = tree.getRootHash()

    transacciones_modificadas = list(transacciones)
    transacciones_modificadas[1] = "TX2: Beto envia 999 BTC a Carla"  # dato alterado
    tree_modificado = MerkleTree(transacciones_modificadas)
    root_modificada = tree_modificado.getRootHash()

    print(f"  Bloque 1 original : {transacciones[1]}")
    print(f"  Bloque 1 alterado : {transacciones_modificadas[1]}")
    print(f"  Root original     : {root_original}")
    print(f"  Root modificada   : {root_modificada}")
    print(f"  ¿La raiz cambio? -> {root_original != root_modificada}")

    # ------------------------------------------------------------------
    # 4) Generar y verificar prueba de inclusión para el bloque 3
    # ------------------------------------------------------------------
    separador("4) Prueba de inclusion para el Bloque 3 (indice 2)")
    indice_objetivo = 2 
    bloque_objetivo = transacciones[indice_objetivo]

    proof = tree.getProof(indice_objetivo)
    print(f"  Bloque objetivo: {bloque_objetivo}")
    print(f"  Longitud de la prueba: {len(proof)} pasos")
    for paso, (sibling, pos) in enumerate(proof):
        print(f"    Paso {paso}: hermano={sibling[:16]}...  posicion={pos}")

    es_valida = MerkleTree.verifyProof(bloque_objetivo, proof, tree.getRootHash())
    print(f"  ¿Prueba valida con el dato correcto? -> {es_valida}")
    visualizar_arbol(tree, proof_index=indice_objetivo, filename="merkle_tree_proof.png")

    # ------------------------------------------------------------------
    # 5) Intentar verificar con un dato incorrecto -> debe fallar
    # ------------------------------------------------------------------
    separador("5) Verificacion con un dato incorrecto -> debe fallar")
    dato_falso = "TX3: Carla envia 7000 BTC a David"  # dato distinto al original
    es_valida_falsa = MerkleTree.verifyProof(dato_falso, proof, tree.getRootHash())
    print(f"  Dato incorrecto: {dato_falso}")
    print(f"  ¿Prueba valida con dato incorrecto? -> {es_valida_falsa}")

    assert es_valida is True, "La prueba deberia ser valida con el dato correcto"
    assert es_valida_falsa is False, "La prueba NO deberia ser valida con datos alterados"

    separador("Todas las verificaciones del experimento pasaron correctamente")


if __name__ == "__main__":
    experimento_merkle()

# Codigo base original sacado de "https://www.geeksforgeeks.org/dsa/introduction-to-merkle-tree/" y contribuido por Pranay Arora (TSEC-2023),
# extendido para incluir punteros de padre, pruebas de inclusion
# y el experimento solicitado.