"""Push a Kaggle kernel with accelerator selection.

Usage:
    python push_kernel.py
    python push_kernel.py --accelerator NvidiaRtxPro6000
"""
import argparse
import subprocess
from pathlib import Path

FOLDER = Path(__file__).parent / "nvidia-competition"
DEFAULT_ACCELERATOR = "NvidiaRtxPro6000"


def push(folder: Path, accelerator: str):
    cmd = [
        "kaggle", "kernels", "push",
        "-p", str(folder),
        "--accelerator", accelerator,
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push Kaggle kernel")
    parser.add_argument(
        "--accelerator",
        default=DEFAULT_ACCELERATOR,
        help=f"Accelerator ID (default: {DEFAULT_ACCELERATOR})",
    )
    parser.add_argument(
        "--folder",
        default=str(FOLDER),
        help=f"Kernel folder (default: {FOLDER})",
    )
    args = parser.parse_args()
    push(Path(args.folder), args.accelerator)
