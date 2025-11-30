import sys

sys.path.insert(0, "src")
import argparse


def run_tk_gui():
    from pedestrian_evacuation.gui.tk import main

    main()

def main():
    parser = argparse.ArgumentParser(
        "pedestrian_evacuation_simulation", usage="python scripts/main.py"
    )
    parser.add_argument("--gui", type=str, default="tk", help="GUI type")
    args = parser.parse_args()

    if args.gui == "tk":
        run_tk_gui()
    else:
        print(f"GUI type [{args.gui}] not recognized.")


if __name__ == "__main__":
    main()
