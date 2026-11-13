# Stellar Collapse Classification: Black Hole or Neutron Star

Predicción del remanente final de estrellas masivas (BH o NS) a partir de
propiedades físicas disponibles antes del colapso, usando los datos de
Sukhbold et al. (2016).

El proyecto se encuentra actualmente en la etapa de preparación y comprensión
de los datos. Todavía no se construyó el dataset Gold ni se entrenaron modelos.

## Estructura

- `data/bronze/`: archivos originales, conservados sin transformar.
- `data/silver/`: tablas intermedias generadas a partir de Bronze.
- `data/gold/`: dataset final de modelado. Permanece vacío hasta definir el target y auditar leakage.
- `src/`: código reutilizable para procesar los datos.
- `notebooks/`: notebooks iniciales para EDA, aprendizaje no supervisado y aprendizaje supervisado.
- `docs/`: paper científico de referencia.

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

Silver no contiene joins duplicados por engine. Gold permanece vacío.

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
de forma exploratoria en `01_eda.ipynb`, pero Gold todavía no fue construido.

Al volver a ejecutar el script, los tres CSV de Silver se sobrescriben de forma
determinística. No se crean copias ni se acumulan filas:

```bash
python src/build_silver.py
```

## Notebooks

- `01_eda.ipynb`: análisis exploratorio en curso de progenitores, outcomes,
  target ponderado y propiedades pre-supernova.
- `02_unsupervised_learning.ipynb`: espacio inicial para el análisis no supervisado.
- `03_supervised_learning.ipynb`: espacio inicial para el modelado supervisado.

Los notebooks de aprendizaje no supervisado y supervisado todavía contienen
solo su estructura inicial.

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
