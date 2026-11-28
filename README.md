# Stellar Collapse Classification: Black Hole or Neutron Star

Estimación del consenso de cuatro modelos de explosión sobre el destino BH o NS
de estrellas masivas, a partir de propiedades físicas anteriores al colapso.
Se usan los datos de Sukhbold et al. (2016). El puntaje predicho describe esas
simulaciones, no una probabilidad observada en estrellas reales.

El análisis exploratorio está completo y ya se generó el dataset Gold.
El notebook supervisado compara configuraciones de una red neuronal con Leave-One-Out y evalúa el modelo elegido en test.

## Estructura

- `data/bronze/`: archivos originales, conservados sin transformar.
- `data/silver/`: tablas intermedias generadas a partir de Bronze.
- `data/gold/`: dataset de modelado generado desde el notebook EDA.
- `src/`: procesamiento de datos y definición de la red neuronal.
- `models/`: pesos y configuración del modelo final.
- `notebooks/`: EDA, análisis no supervisado, modelado supervisado y resumen ejecutable.
- `docs/`: paper de referencia, informe final en PDF y figuras.

## Tablas Silver

- `progenitor_features.csv`: propiedades físicas pre-supernova. Contiene las features candidatas.
- `engine_outcomes.csv`: resultados BH/NS y variables de la explosión por engine. Se usa para construir el target, no como matriz de features.
- `auxiliary_yields.csv`: cantidades de elementos químicos expulsados en vientos estelares y durante la explosión. No se usan como features porque los resultados de la explosión generarían leakage.

El script `src/build_silver.py` reconstruye estas tres tablas desde Bronze. Al
normalizar los nombres de cuatro progenitores de Woosley & Heger (2015), conserva
el nombre original en `result_model_name` y usa el identificador común en `model`.
Las masas de los núcleos de helio y CO se calculan con los límites de composición
de la Tabla 2 de Sukhbold et al. (2016). Los valores `---` de los perfiles
originales se conservan como faltantes en Silver.

Silver no contiene joins duplicados por engine.

`progenitor_features.csv` tiene 200 filas, una por estrella antes del colapso.
Trece progenitores de menor masa fueron procesados solo con Z9.6.
Los otros 187 tienen resultados en los cinco engines restantes.

Para el target se eligieron cuatro engines: N20 (peso 0.30), W18 (0.30),
W15 (0.20) y S19.8 (0.20). N20 y W18 tienen mayor peso porque son los dos
engines en los que se centra principalmente el paper. W20 se conserva en
Silver, pero no forma parte de esta combinación. El paper lo identifica como
el engine más débil, con más explosiones fallidas, y justifica excluirlo de
su análisis de nucleosíntesis, es decir, de producción de elementos químicos
(Sukhbold et al., 2016, pp. 16-18).
Los pesos son una decisión de este proyecto. El target ponderado se calcula
en `01_eda.ipynb` y se guarda en Gold.

## Dataset Gold

`data/gold/progenitor_gold.csv` tiene 187 filas, una por progenitor, y 46
columnas: `model`, 44 propiedades físicas pre-supernova y `target_score`.
`model` es un identificador y `target_score` es el objetivo del modelo.
Los outcomes individuales permanecen en Silver para poder auditar el target.

El EDA excluye `surface_fe56` porque todos sus valores son faltantes,
`zone_count` porque describe la resolución del archivo y `progenitor_family`
porque es constante entre estas 187 estrellas. Las estimaciones de masa de
núcleo sin una definición respaldada por los datos originales se quitaron
de Silver. El resto de las features físicas se conserva, aunque algunas están
muy correlacionadas.

La última celda del notebook EDA vuelve a generar el CSV y lo sobrescribe si
ya existe.

Al volver a ejecutar el script, los tres CSV de Silver se sobrescriben de forma
determinística. No se crean copias ni se acumulan filas:

```bash
python src/build_silver.py
```

## Notebooks

- `01_eda.ipynb`: análisis exploratorio de progenitores, outcomes, target
  ponderado y propiedades pre-supernova. Genera el CSV Gold.
- `02_unsupervised_learning.ipynb`: explora Gold con PCA y K-Means++.
- `03_supervised_learning.ipynb`: separación estratificada, comparación de arquitecturas, curvas de pérdida, entrenamiento final y evaluación en test de una MLP en PyTorch.
- `04_project_summary.ipynb`: resultados principales y una celda final para predecir desde un CSV con el modelo guardado. Se puede leer sin volver a entrenar.

Las figuras de los tres notebooks de análisis se guardan en `docs/figures/`.

## Predicciones

La última celda de `04_project_summary.ipynb` carga el modelo guardado en
`models/stellar_collapse_mlp.pt`. Cambiar `INPUT_CSV` por la ruta del archivo
que se quiera predecir. Debe contener las mismas 44 propiedades físicas que Gold;
`model` es opcional y `target_score` no hace falta. La celda guarda un CSV con
`predicted_score` y `predicted_class` (NS o BH según el umbral 0.5).

## Entorno

En macOS, crear un entorno virtual local llamado `.SCC`:

```bash
python3 -m venv .SCC
source .SCC/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para salir del entorno:

```bash
deactivate
```
