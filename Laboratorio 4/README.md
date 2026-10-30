# Consultas de entregas con Quadtree

## Juan Esteban Valencia Quintero 

## Objetivo

El objetivo de este proyecto es implementar y evaluar un Quadtree para
organizar puntos de entrega ubicados en una ciudad de 10 km x 10 km. El
proyecto permite realizar consultas para encontrar entregas cercanas a una ubicación y comparar el rendimiento del Quadtree con una búsqueda tradicional.

También se generan pruebas, gráficas y un análisis del comportamiento del programa con diferentes cantidades de puntos.

## Código de Honor

Para este proyecto se tomaron en cuenta varias referencias y el uso de inteligencia artificial.

Referencias:
  - https://www.youtube.com/watch?v=OJxEcs0w_kE
  - https://www.youtube.com/watch?v=QQx_NmCIuCY
  - https://en.wikipedia.org/wiki/Quadtree
  - https://www.geeksforgeeks.org/dsa/quad-tree/

Para que se uso IA:
Se hizo uso de IA para la modificación de el código del Quadtree y la realización del código de fuerza bruta. Además se uso para la creacioón de las graficas, la creación de `analisis.py` y `test.py`.

## Contenido del proyecto

- `Quadtree.py`: contiene la implementación principal del Quadtree, las estructuras utilizadas para representar los puntos y las regiones, y las funciones de búsqueda.
- `test.py`: ejecuta las pruebas del proyecto y genera las visualizaciones relacionadas con las consultas y la distribución de los puntos.
- `analisis.py`: realiza una comparación de rendimiento entre el Quadtree y la búsqueda por fuerza bruta para diferentes tamaños de datos.
- `radio_vecinos.png`: muestra los puntos encontrados dentro de un radio de búsqueda.
- `vecino_mas_cercano.png`: muestra la consulta del vecino más cercano.
- `divisiones_quadtree.png`: muestra la división espacial generada por el Quadtree.
- `benchmark.png`: muestra los resultados del análisis de rendimiento.

## Requisitos

- Python 3.9 o una versión posterior.
- `matplotlib`, utilizada para generar las gráficas.

Para instalar la dependencia, se puede ejecutar:

```bash
pip install matplotlib
```

## Ejecución

Desde la carpeta del proyecto, ejecutar:

```bash
python test.py
```

Este comando ejecuta las pruebas y genera las visualizaciones del proyecto.

Para ejecutar el análisis comparativo de rendimiento:

```bash
python analisis.py
```

El programa utiliza datos generados de manera reproducible. Si se desea repetir una ejecución con una ubicación de consulta específica, se puede cambiar el valor la variable `QUADTREE_SEED` antes de ejecutar `test.py`:

```powershell
$env:QUADTREE_SEED = "123"
python test.py
```
