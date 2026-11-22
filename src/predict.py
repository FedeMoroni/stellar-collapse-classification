import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

if __package__:
    from .model import StellarCollapseMLP
else:
    from model import StellarCollapseMLP


def predict(input_path, model_path):
    data = pd.read_csv(input_path)
    saved = torch.load(model_path, map_location="cpu", weights_only=True)
    features = saved["feature_names"]

    values = data[features].to_numpy(dtype=np.float32)
    mean = np.array(saved["scaler_mean"], dtype=np.float32)
    scale = np.array(saved["scaler_scale"], dtype=np.float32)
    inputs = torch.from_numpy((values - mean) / scale)

    model = StellarCollapseMLP(len(features), saved["hidden_sizes"])
    model.load_state_dict(saved["state_dict"])
    model.eval()

    with torch.no_grad():
        scores = torch.sigmoid(model(inputs)).numpy().ravel()

    result = pd.DataFrame({
        "predicted_score": scores,
        "predicted_class": np.where(scores >= saved["threshold"], "BH", "NS"),
    })
    if "model" in data.columns:
        result.insert(0, "model", data["model"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="CSV with the same feature columns as Gold")
    parser.add_argument("output", help="CSV for the predictions")
    parser.add_argument(
        "--model-path",
        default=Path(__file__).resolve().parents[1] / "models" / "stellar_collapse_mlp.pt",
    )
    args = parser.parse_args()

    predict(args.input, args.model_path).to_csv(args.output, index=False)
    print(f"Saved predictions: {args.output}")
