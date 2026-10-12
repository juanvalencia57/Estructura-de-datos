## Juan Esteban Valencia Quintero
# Estudio experimental de índices de búsqueda

Este proyecto compara tres formas de almacenar y consultar registros de
estudiantes:

- **Secuencia de Python**: búsqueda secuencial y ordenamiento de una lista.
- **Árbol binario de búsqueda**: árbol binario de búsqueda sin balanceo.
- **Árbol B+**: árbol balanceado con hojas enlazadas.

El experimento mide búsquedas puntuales, consultas por rango, recorridosordenados y diferentes tamaños de lotes de consultas. También compara datos insertados en orden mezclado con datos insertados en orden creciente.

## Código de honor

Se consultaron las siguientes referencias:

- <https://www.geeksforgeeks.org/python/binary-search-tree-in-python/>
- <https://www.geeksforgeeks.org/dsa/b-tree-in-python-2/>

Se utilizó asistencia de IA para:

- Adaptar las implementaciones de los árboles y la secuencia a los requisitos del proyecto.
- Implementar y dar formato a las gráficas.
- Se hizo con IA experimento_indices y validar_distribucion.
- Mejorar las explicaciones y las instrucciones de ejecución del README.

## Archivos principales

`estructura_bplus.py` Implementación del árbol B+. 
`indice_binario.py` Implementación del árbol binario de búsqueda sin balanceo. 
`datos_sinteticos.py` Generación reproducible de registros de estudiantes. 
`experimento_indices.py` Mediciones, exportación a CSV y gráficas.  `validar_distribucion.py`  Análisis Shapiro-Wilk de las muestras de tiempo. 

## Diseño del experimento

Cada registro contiene un identificador, nombre, edad y promedio. Una semilla aleatoria fija permite reproducir los datos generados. Cada tamaño de conjunto se prueba con datos mezclados y con datos ordenados por identificador.

La configuración de `experimento_indices.py` es:

- `N = 4800, 6000, 7200, ..., 19200` (13 tamaños de conjunto).
- 25 repeticiones por cada punto del experimento.
- Hasta 1500 identificadores aleatorios para las búsquedas puntuales.
- Consultas por rango que cubren el 2%, 8%, 15% y 30% de los identificadores.
- Lotes de 40 llamadas para consultas por rango y recorridos ordenados.
- Un conjunto fijo de `N = 6000` para el experimento de lotes de consultas.
- Lotes de consultas de `M = 25, 100, 250, 750, 1500`.

El tiempo transcurrido se mide con `time.perf_counter_ns()`. Los scripts guardan la mediana, el promedio, la desviación estándar, el mínimo, el máximo, el percentil 25 y el percentil 75. Las gráficas utilizan la mediana y barras de error asimétricas del intervalo intercuartílico; las mediciones no se suavizan ni se reemplazan con datos teóricos.

## Gráficas generadas

Todas las gráficas se guardan en `Resultados/`. El experimento actual genera:

- `figura_lookups_only.png`: búsquedas puntuales con las estructuras ya
  construidas.
- `figura_build_and_lookup.png`: construcción de la estructura seguida de
  búsquedas puntuales.
- `figura_range_02pct.png`, `figura_range_08pct.png`,
  `figura_range_15pct.png` y `figura_range_30pct.png`: costos de las consultas
  por rango.
- `figura_ordered_scan.png`: listado completo ordenado por identificador.
- `panel_comparativo_loglog.png`: resumen con ambos ejes logarítmicos.
- `panel_comparativo_semilog.png`: resumen con `N` en escala logarítmica y
  tiempo en escala lineal.
- `figura_consultas_por_lote.png`: tiempo total para cada tamaño de lote.
- `figura_huella_por_consulta.png`: tiempo promedio por consulta en cada lote.

Los puntos y las barras de error provienen directamente de las mediciones. Las gráficas no agregan datos interpolados ni datos teóricos.

## Archivos de datos

El experimento genera los siguientes archivos:

- `Resultados/mediciones_resumen.csv`: una fila por experimento, orden de
  entrada y estructura, con medianas y desviaciones estándar para cada `N`.
- `Resultados/mediciones_detalladas.csv`: una fila por cada valor de `N`.
- `Muestreo_estadistico/muestras_crudas.csv`: cada muestra individual de
  tiempo.
- `Muestreo_estadistico/evaluacion_normalidad.csv`: resultados de Shapiro-Wilk
  generados por `validar_distribucion.py`.

## Instalación y ejecución

Ejecuta estos comandos desde la carpeta del proyecto:

```powershell
python -m pip install -r requirements.txt
python experimento_indices.py
python validar_distribucion.py
```

El primer script genera las mediciones, los archivos CSV y las gráficas. El segundo lee `Muestreo_estadistico/muestras_crudas.csv` y escribe
`Muestreo_estadistico/evaluacion_normalidad.csv` utilizando `alpha = 0.05`.

El experimento completo puede tardar varios minutos o más porque realiza muchas repeticiones sobre conjuntos grandes. El script de validación estadística debe ejecutarse después de que el experimento haya generado
`muestras_crudas.csv`.

También se pueden indicar los archivos manualmente:

```powershell
python validar_distribucion.py `
  --raw Muestreo_estadistico/muestras_crudas.csv `
  --out Muestreo_estadistico/evaluacion_normalidad.csv `
  --alpha 0.05
```

## Hardware y software

Los tiempos dependen del equipo, del sistema operativo y de los procesos en segundo plano. Por ejemplo, en el PC de un amigo se demoró 2 horas en ejecutar, pero era porque estábamos haciendo muchas cosas en el PC; en mi PC se demoró 40 minutos solo teniendo Visual Studio Code abierto, pero jugando se demoró 1 hora y 30 minutos. Para registrar el entorno exacto antes de medir, se pueden ejecutar los siguientes comandos:

```powershell
python --version
python -c "import matplotlib, scipy; print(matplotlib.__version__); print(scipy.__version__)"
Get-CimInstance Win32_Processor | Select-Object Name
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
```

Las mediciones solo deben compararse directamente cuando se obtienen bajo condiciones equivalentes de hardware y software.

## Interpretación

Las búsquedas puntuales en la secuencia generalmente aumentan con `N`. El árbol binario puede comportarse aproximadamente como `O(log N)` con
inserciones mezcladas, pero las inserciones ordenadas pueden degenerarlo hasta formar una cadena larga. El árbol B+ conserva una altura balanceada y es menos sensible al orden de inserción. El costo de las consultas por rango y de los recorridos ordenados también depende de la cantidad de registros devueltos.

Estas conclusiones describen las implementaciones, los tamaños de entrada y el entorno utilizados en este proyecto. No son garantías para cualquierconfiguración de hardware o distribución de datos.