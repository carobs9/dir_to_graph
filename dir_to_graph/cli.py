import argparse
import os

from .core import DEFAULT_IGNORES, write_tree_json


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dir-to-graph",
        description=(
            "Generate a data.json file for a directory tree so it "
            "can be visualized with the bundled index.html (D3)."
        ),
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help=(
            "Directory where data.json is written. "
            "Defaults to the current working directory (e.g. your dir_to_graph repo)."
        ),
    )

    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        default=None,
        help=(
            "Directory name to ignore. Can be passed multiple times. "
            f"Defaults: {', '.join(DEFAULT_IGNORES)}"
        ),
    )

    parser.add_argument(
        "--max-seconds",
        type=float,
        default=15.0,
        help=(
            "Time budget in seconds for computing folder sizes. "
            "After this, the tool stops walking for sizes and continues "
            "with unknown sizes (shown as 0 in the visualization). "
            "Set to 0 to disable the limit."
        ),
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    BANNER = """
                                                               ▄▄    
   ██ ▀▀              ██                                       ██    
▄████ ██  ████▄      ▀██▀▀ ▄███▄       ▄████ ████▄  ▀▀█▄ ████▄ ████▄ 
██ ██ ██  ██ ▀▀ ▀▀▀▀▀ ██   ██ ██ ▀▀▀▀▀ ██ ██ ██ ▀▀ ▄█▀██ ██ ██ ██ ██ 
▀████ ██▄ ██          ██   ▀███▀       ▀████ ██    ▀█▄██ ████▀ ██ ██ 
                                          ██             ██          
                                        ▀▀▀              ▀▀          
"""
    print(BANNER)

    print("═════════════════════════════════════════════════════════════════════════════════════════════════════════")
    print()
    print("Welcome! This project allows you to visualize directory structures as interactive graphs.")
    print("This is still an experimental tool; please report any issues you encounter.")
    print("Directories containing many big files may take a while to process.")
    print()
    print("═════════════════════════════════════════════════════════════════════════════════════════════════════════")

    args = parse_args(argv) # parse command-line arguments
    target_dir = os.path.abspath(args.path) # get absolute path of target directory

    print()
    print(f"Now, I will analyze your directory ({target_dir}) and generate the visualization data...")
    print()

    if not os.path.isdir(target_dir): # check if target path is a directory
        raise SystemExit(f"Not a directory: {target_dir}") # if not a directory, exit with error

    ignore = args.ignore if args.ignore is not None else DEFAULT_IGNORES # set ignore list

    # By default, write data.json into the current working directory
    # (typically your dir_to_graph repo where index.html lives).
    output_dir = os.path.abspath(args.output_dir or os.getcwd()) # determine output directory
    out_path = write_tree_json( # write tree JSON to disk
        target_dir, # analyze provided target directory
        output_dir=output_dir, # store in the provided output directory
        filename="data.json", # fixed filename
        ignore=ignore, # directories to ignore
        max_seconds=args.max_seconds if args.max_seconds and args.max_seconds > 0 else None, # time budget for size calculation
    )

    print(f"[INFO] Wrote directory structure as a JSON: {out_path}")
    print()
    print("Next steps:")
    print("  1.  python -m http.server 8000")
    print("  2.  Open http://localhost:8000/index.html in your browser")


if __name__ == "__main__": 
    main()
