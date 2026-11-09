# Stellar Collapse Classification: Black Hole or Neutron Star

Predicción del remanente final de estrellas masivas (BH o NS) a partir de
propiedades físicas disponibles antes del colapso, usando los datos de
Sukhbold et al. (2016).

El proyecto se encuentra actualmente en la etapa de preparación y comprensión
de los datos. Todavía no se construyó el dataset Gold ni se entrenaron modelos.

## Estructura

- `data/bronze/`: archivos originales, conservados sin transformar.
- `data/silver/`: tablas intermedias generadas a partir de Bronze.
- `data/gold/`: dataset final de modelado; permanece vacío hasta definir el target y auditar leakage.
- `src/`: código reutilizable para procesar los datos.
- `notebooks/`: notebooks iniciales para EDA, aprendizaje no supervisado y aprendizaje supervisado.
- `docs/`: paper científico de referencia.

## Tablas Silver

- `progenitor_features.csv`: propiedades físicas pre-supernova; contiene las features candidatas.
- `engine_outcomes.csv`: resultados BH/NS y variables de explosión por engine; se usa para construir el target, no como matriz de features.
- `auxiliary_yields.csv`: rendimientos de nucleosíntesis; se conserva como información auxiliar y queda fuera del modelo.

El script `src/build_silver.py` reconstruye estas tres tablas desde Bronze. Al
normalizar los nombres de cuatro progenitores de Woosley & Heger (2015), conserva
el nombre original en `result_model_name` y usa el identificador común en `model`.

Silver no contiene joins duplicados por engine. Gold permanece vacío.

Al volver a ejecutar el script, los tres CSV de Silver se sobrescriben de forma
determinística; no se crean copias ni se acumulan filas:

```bash
python src/build_silver.py
```

## Notebooks

- `01_eda.ipynb`: espacio inicial para el análisis exploratorio.
- `02_unsupervised_learning.ipynb`: espacio inicial para el análisis no supervisado.
- `03_supervised_learning.ipynb`: espacio inicial para el modelado supervisado.

Los notebooks solo contienen su estructura inicial. El análisis todavía no comenzó.

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
