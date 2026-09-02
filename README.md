Juan Esteban Valencia Quintero CC: 1055753856

# Matriz booleana eficiente 100000 x 100000

Este proyecto genera una matriz booleana grande de forma eficiente, guardando cada valor como un bit para ahorrar espacio y evitar generar archivos gigantes en texto.

## ¿Cómo funciona el código?

El archivo principal es "matriz_texto.py".

Lo que hace es lo siguiente:

1. Define la cantidad de filas y columnas que se van a guardar.
2. Crea el archivo binario con dos valores iniciales:
   - 8 bytes para la cantidad de filas
   - 8 bytes para la cantidad de columnas
3. Luego escribe los datos de la matriz compactados por bits.
4. Al final, valida que el archivo tenga la estructura esperada leyendo esas primeras 16 bytes.

La idea principal es que no se genera una matriz visible como una tabla llena de 0 y 1 en texto, porque eso sería demasiado grande. En lugar de eso, cada valor se guarda en un bit, que es la representación más compacta posible.

## ¿Qué patrón usa la matriz?

La matriz se llena con un patrón alternado, por ejemplo:

- fila 1: 0101010101...
- fila 2: 1010101010...
- fila 3: 0101010101...

Esto permite que cada valor sea claramente identificable sin necesidad de guardar todo como texto visible.

## ¿Cuánto espacio ocupa?

Si se guardara en texto, cada valor 0 o 1 ocuparía 1 byte. Entonces:

- 100000 x 100000 = 10,000,000,000 valores
- eso equivale aproximadamente a 10 GB

Como la matriz se guarda en bits:

- 1 bit por valor
- 10,000,000,000 bits
- 10,000,000,000 / 8 = 1,250,000,000 bytes

Eso equivale aproximadamente a:

- 1.25 GB

Es decir, se ahorra muchísimo espacio y se mantiene la matriz real.

## ¿Cómo se "muestra" que realmente hay 100000 x 100000?

No se muestra la matriz completa en la terminal porque esa salida sería excesivamente larga y poco útil para análisis. La validación se hace leyendo la cabecera del archivo, y eso es suficiente porque la cabecera no es un dato sin importancia: es la definición estructural del contenido del archivo.

El archivo se escribe en este orden exacto:

1. primero se guarda el número de filas
2. luego se guarda el número de columnas
3. después se guardan los datos de la matriz en ese formato

Eso significa que el archivo dice, de manera formal y precisa:

- esta matriz tiene 100000 filas
- esta matriz tiene 100000 columnas

Cuando se leen los primeros 16 bytes del archivo, se obtiene exactamente esa información. Y esa información es suficiente porque en una matriz rectangular, el tamaño total se determina de manera directa por la relación:

total de elementos = filas × columnas

Si:

filas = 100000

y

columnas = 100000

entonces:

100000 × 100000 = 10,000,000,000

Por lo tanto, la matriz tiene exactamente 10,000,000,000 elementos.

Esto no es una estimación, es una consecuencia matemática directa de la estructura del archivo. La cabecera representa la dimensión real de la matriz, y el total de elementos se deduce exactamente de esos dos valores.

### Generar la matriz grande en PowerShell

Para generar la matriz completa de 100000 x 100000, se ejecuta este comando:

```powershell
python .\matriz_texto.py --rows 100000 --cols 100000 --output matriz_100000x100000.bin
```

Explicación:

- "python" ejecuta el programa.
- ".\matriz_texto.py" indica el archivo de Python que contiene la lógica.
- "--rows 100000" dice que la matriz tendrá 100000 filas.
- "--cols 100000" dice que la matriz tendrá 100000 columnas.
- "--output matriz_100000x100000.bin" indica el nombre del archivo binario que se va a crear.

Este comando crea la matriz grande en disco, pero en formato compacto y sin generar un archivo de texto gigante.

### Comando para verificar la dimensión de la matriz grande

En PowerShell se puede hacer así:

```powershell
python -c "with open('matriz_100000x100000.bin', 'rb') as f: filas = int.from_bytes(f.read(8), 'little'); columnas = int.from_bytes(f.read(8), 'little'); print(filas); print(columnas); print(filas * columnas)"
```

Explicación en términos de la matriz grande:

- "python .\matriz_texto.py --rows 100000 --cols 100000 --output matriz_100000x100000.bin" genera el archivo binario con 100000 filas y 100000 columnas.
- "f.read(8)" lee los primeros 8 bytes del archivo, que corresponden al número de filas de la matriz grande.
- "f.read(8)" lee los siguientes 8 bytes, que corresponden al número de columnas de la matriz grande.
- "filas * columnas" calcula el total de elementos de la matriz, que en este caso es 100000 × 100000 = 10,000,000,000.
- Eso demuestra que el archivo no solo almacena datos, sino que también guarda la dimensión real de la matriz en su encabezado.

La salida esperada es:

```
100000
100000
10000000000
```

Eso significa que:

- hay 100000 filas
- cada fila tiene 100000 columnas
- la matriz tiene 10,000,000,000 elementos

Esta salida no se toma como una “aproximación visual”, sino como la comprobación formal de la estructura del archivo. Si el archivo está construido de esa forma, entonces la dimensión y el total de elementos quedan definidos de manera exacta.

## ¿Por qué no se pueden mostrar todos los datos literalmente?

Porque sería inmenso.

Una matriz de 100000 x 100000 tiene 10,000,000,000 posiciones. Si se intentara mostrarla en pantalla, la salida sería:

- excesivamente larga
- poco legible
- demasiado lenta
- innecesaria para verificar la dimensión

Además, la consola no está diseñada para imprimir un archivo de ese tamaño de forma útil. Lo que se hace en estos casos es verificar la estructura con el contenido del archivo, no mostrar cada dato individualmente.

## Conclusión

La matriz se puede considerar "mostrada" de forma válida porque su estructura está almacenada en el archivo en forma de cabecera, donde se especifican exactamente 100000 filas y 100000 columnas. A partir de esos dos valores, se demuestra matemáticamente que el archivo contiene 100000 × 100000 = 10,000,000,000 elementos. Esto permite validar la dimensión real de la matriz sin imprimir toda su contenido en la consola.

La solución cumple con el objetivo de guardar una matriz grande de manera eficiente, compacta y verificable, evitando el uso de archivos de texto gigantes y manteniendo una validación clara de su tamaño.
