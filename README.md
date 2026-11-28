# Stellar Collapse Classification: Black Hole or Neutron Star

This project estimates the agreement of four explosion engines on whether a
massive star forms a black hole (BH) or a neutron star (NS). It uses the star's
physical properties before collapse and data from Sukhbold et al. (2016). The
predicted score describes agreement between simulations, not a calibrated
probability for a real star.

The notebooks cover data exploration, unsupervised analysis, model selection,
and evaluation. A shorter notebook presents the main results and runs the saved
model on a CSV file.

For a quick overview, start with the [project summary](notebooks/04_project_summary.ipynb).
The [report](docs/stellar_collapse_report.pdf) gives the full method and results.

## Project structure

- `data/bronze/`: original files, kept without changes.
- `data/silver/`: intermediate tables built from Bronze.
- `data/gold/`: modeling dataset built in the EDA notebook.
- `src/`: data processing and neural network definition.
- `models/`: weights and settings of the final model.
- `notebooks/`: EDA, unsupervised learning, supervised learning, and a runnable summary.
- `docs/`: reference paper, final report in PDF, and figures.

## Silver tables

- `progenitor_features.csv`: physical properties before the supernova. It contains candidate input features.
- `engine_outcomes.csv`: BH/NS outcomes and explosion properties for each engine. The outcomes are used to build the target, not as model inputs.
- `auxiliary_yields.csv`: elements expelled in stellar winds and during the explosion. They are not model inputs because explosion results would leak information about the outcome.

The `src/build_silver.py` script rebuilds these three tables from Bronze. When
it standardizes the names of four Woosley & Heger (2015) progenitors, it keeps
the original name in `result_model_name` and uses the shared ID in `model`.
Helium and CO core masses are calculated from the composition limits in Table 2
of Sukhbold et al. (2016). Values marked `---` in the original profiles remain
missing in Silver.

Silver has no duplicate joins by engine.

`progenitor_features.csv` has 200 rows, one per star before collapse. Thirteen
lower-mass progenitors were processed only with Z9.6. The other 187 have
outcomes from the remaining five engines.

Four engines were chosen for the target: N20 (weight 0.30), W18 (0.30), W15
(0.20), and S19.8 (0.20). N20 and W18 have higher weights because they are the
two engine series that the paper focuses on most. W20 remains in Silver but is
not part of this target. The paper describes it as the weakest engine, with
more failed explosions, and excludes it from its nucleosynthesis analysis
(Sukhbold et al., 2016, pp. 16–18). The weights are a choice made for this
project. The weighted target is calculated in `01_eda.ipynb` and saved in Gold.

## Gold dataset

`data/gold/progenitor_gold.csv` has 187 rows, one per progenitor, and 46
columns: `model`, 44 physical properties before the supernova, and
`target_score`. `model` is an ID, and `target_score` is the model's target.
Individual engine outcomes remain in Silver so the target can be checked.

The EDA excludes `surface_fe56` because all its values are missing,
`zone_count` because it describes the profile resolution, and
`progenitor_family` because it has the same value for all 187 stars. Core-mass
estimates without a definition supported by the original data were removed
from Silver. The other physical features are kept, although some are strongly
correlated.

The last cell of the EDA notebook regenerates the Gold CSV and overwrites it if
it already exists.

Running the script again overwrites the three Silver CSV files in the same
way. It does not create copies or add duplicate rows:

```bash
python src/build_silver.py
```

## Notebooks

- `01_eda.ipynb`: explores progenitors, engine outcomes, the weighted target, and physical properties before collapse. It creates the Gold CSV.
- `02_unsupervised_learning.ipynb`: explores Gold with PCA and K-Means++.
- `03_supervised_learning.ipynb`: uses a stratified split, compares network architectures, shows loss curves, trains the final PyTorch MLP, and evaluates it on the test set.
- `04_project_summary.ipynb`: presents the main results and has a final cell that predicts from a CSV with the saved model. It can be read without training the model again.

The figures from the three analysis notebooks are saved in `docs/figures/`.

## Predictions

The last cell of `04_project_summary.ipynb` loads the saved model from
`models/stellar_collapse_mlp.pt`. Set `INPUT_CSV` to the path of the file you
want to predict. It must contain the same 44 physical feature columns as Gold;
`model` is optional, and `target_score` is not needed. The cell writes a CSV
with `predicted_score` and `predicted_class` (NS or BH using the 0.5 cutoff).

## Environment

Use a virtual environment on macOS, Linux, or Windows. From the project root:

### macOS and Linux (bash or zsh)

```bash
python3 -m venv .SCC
source .SCC/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .SCC
.\.SCC\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In Windows Command Prompt, activate the environment with `.SCC\Scripts\activate.bat` instead.

To leave the environment on any system:

```bash
deactivate
```
