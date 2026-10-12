# Árbol de Merkle

Este proyecto implementa un árbol de Merkle en Python usando SHA-256. El código principal está en `Merkle.py`.

Cada bloque se convierte en un hash y los hashes se combinan hasta obtener un único resultado llamado **Merkle Root**. Si se modifica un bloque, la raíz también cambia.

## Código de honor

El código se basó en la explicación y el ejemplo de [GeeksforGeeks](https://www.geeksforgeeks.org/dsa/introduction-to-merkle-tree/). Tambien se utilizó IA generativa para modificar el código y cumplir los requisitos que se pedian en el laboratorio y en algunas partes de este README, para que algunas cosas quedaran explicadas de una manera clara.

Se uso IA generativa para modificar el código y que cumpla con lo siguiente:

    - Crear 5 bloques de datos (transacciones simuladas)
    - Construir el árbol y mostrar la raíz.
    - Modificar un bloque y demostrar que la raíz cambia.
    - Generar una prueba de inclusión para el bloque 3 y verificar que es válida.
    - Intentar verificar con un dato incorrecto → debe fallar.

Se uso IA generativa en la siguiente parte del README:

    - Verificaciones (validas e invalidas) 

## Funcionamiento

El programa hace lo siguiente:

1. Crea cinco bloques con transacciones simuladas:
   - `TX1: Ana envia 10 BTC a Beto`
   - `TX2: Beto envia 3 BTC a Carla`
   - `TX3: Carla envia 7 BTC a David`
   - `TX4: David envia 1 BTC a Elena`
   - `TX5: Elena envia 5 BTC a Ana`
2. Construye el árbol y muestra la Merkle Root.
3. Modifica un bloque y demuestra que la raíz cambia.
4. Genera una prueba de inclusión para el bloque 3.
5. Verifica la prueba con un dato correcto y con uno incorrecto.

La clase `Node` representa los nodos y calcula los hashes. `MerkleTree` construye el árbol, obtiene la raíz y genera las pruebas de inclusión. Cuando un nivel tiene un número impar de nodos, se duplica el último para completarlo.

## Generación de árbol 

El programa genera `merkle_tree.png` y `merkle_tree_proof.png` usando `matplotlib`. Si no se generan los graficos es porque no se tiene descargado `matplotlib`. Si quiere ver el grafico tiene que instalarlo usando el siguiente comando: 

```python
pip install matplotlib
```

## Verificaciones (validas e invalidas)

La verificacion es **valida** cuando se genera la prueba de inclusion (`getProof`) para un bloque y se verifica (`verifyProof`) usando exactamente el mismo dato original. El algoritmo reconstruye el camino hash a hash hasta la raiz y, como el dato no cambio, el resultado coincide con la Merkle Root -> `True` y se genera mi `merkle_tree_proof.png`.

La verificacion es **invalida** cuando se intenta verificar un dato que fue alterado (por ejemplo, cambiando "7 BTC" por "70 BTC"). Al modificar el contenido, su hash SHA-256 cambia por completo, y al reconstruir el camino hasta la raiz el resultado ya no coincide con la Merkle Root -> `False` (se agrega una captura de pantalla para la prueba invalida).

Esto demuestra que el Arbol de Merkle detecta cualquier alteracion en los datos, sin importar que tan pequeña sea.

**Ejemplo:**
- Dato correcto: `TX3: Carla envia 7 BTC a David` -> `True`
- Dato alterado: `TX3: Carla envia 70 BTC a David` -> `False`

## Bloque objetivo

Puntos:

4. Generar una prueba de inclusión para el bloque 3 y verificar que es válida.
5. Intentar verificar con un dato incorrecto → debe fallar.

La prueba del punto 5 usa el indice_objetivo del punto 4:

```python
indice_objetivo = 2
```

La prueba de verificar con un dato incorrecto, es con el bloque objetivo `TX3: Carla envia 7 BTC a David`. El texto original de `TX3` produce `True`.

En cambio, `TX3: Carla envia 7000 BTC a David` produce `False` porque fue alterado. `TX1: Ana envia 10 BTC a Beto` también produce `False` porque pertenece al índice `0`, no al índice `2`, es decir, que si se quiere hacer la prueba con otro bloque que no sea el que me pide el laboratorio, se tiene que cambiar el indice_objetivo del punto 4, lo que también cambiara el resultado de la prueba de inclusión y mi `merkle_tree_proof.png`.

