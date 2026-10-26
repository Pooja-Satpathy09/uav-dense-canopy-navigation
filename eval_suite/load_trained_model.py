
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / "simulator" / "DiffPhysDrone"

sys.path.insert(0, str(SIMULATOR))

from model import Model


def load_trained_model(checkpoint_path):
    checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        raise FileNotFoundError(checkpoint_path)

    # Only load checkpoint files you created or trust.
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False
    )

    if isinstance(checkpoint, dict) and "model" in checkpoint:
        state_dict = checkpoint["model"]
        iteration = checkpoint.get("iteration", "Unknown")
        config = checkpoint.get("config", {})
    else:
        state_dict = checkpoint
        iteration = "Unknown"
        config = {}

    # Match the model configuration used during training.
    no_odom = config.get("no_odom", False)

    if no_odom:
        model = Model(dim_obs=7, dim_action=6)
    else:
        model = Model(dim_obs=10, dim_action=6)

    model.load_state_dict(state_dict, strict=True)
    model.eval()

    print("Model loaded successfully!")
    print("Training iteration:", iteration)
    print("Odometry disabled:", no_odom)

    return model, iteration, config


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python eval_suite/load_trained_model.py "
            "<checkpoint_path>"
        )

    model, iteration, config = load_trained_model(
        sys.argv[1]
    )

    # Dummy input to test neural network execution.
    observation = torch.zeros(1, 1, 12, 16)

    dim_obs = model.v_proj.in_features
    state = torch.zeros(1, dim_obs)

    with torch.no_grad():
        action, values, hidden = model(
            observation, state, None
        )

    print("Observation shape:", tuple(observation.shape))
    print("State shape:", tuple(state.shape))
    print("Action output shape:", tuple(action.shape))
    print("Hidden state shape:", tuple(hidden.shape))
    print("Predictions finite:", torch.isfinite(action).all().item())

    assert action.shape == (1, 6)
    assert torch.isfinite(action).all()

    print("CPU model forward-pass test passed!")
