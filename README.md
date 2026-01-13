![dir_to_graph_logo](assets/dir_to_graph.png)

Visualize any folder on your machine as an interactive tree in the browser.

This project provides:
- a small CLI (`dir-to-graph`) that walks a directory and writes a `data.json` file
- an HTML/D3 viewer (`index.html`) that reads `data.json` and renders a zoomable tree

The graph shows folders and files, with node size roughly proportional to size on disk.

## Requirements

Python 3.10+ and a few Python libraries:

```bash
pip install -r requirements.txt
```

`requirements.txt` currently includes:

- networkx
- matplotlib
- graphviz
- numpy

> Note: the core CLI only needs `networkx` and `numpy`; the others are used in notebooks and experiments.

## Basic usage (from source)

From the repository root:

```bash
cd /Users/caro/Desktop/GITHUB-REPOS/dir_to_graph
python main.py /path/to/your/directory -o .
```

What this does:

- runs the CLI banner and help text
- walks `/path/to/your/directory` (recursively)
- builds a tree representation with per‑node metadata
- writes a D3‑friendly JSON file named `data.json` into the output directory (`-o .` = current directory)

You should see a message like:

```text
[INFO] Wrote directory structure as a JSON: /…/dir_to_graph/data.json
Next steps:
	1.  cd /…/dir_to_graph
	2.  python -m http.server 8000
	3.  Open http://localhost:8000/index.html in your browser
```

Then follow those steps to start a local web server and open the visualization.

## CLI options

The CLI entrypoint is implemented in [dir_to_graph/cli.py](dir_to_graph/cli.py) and exposed via `main.py`.

Usage:

```bash
python main.py [PATH] [-o OUTPUT_DIR] [-i NAME ...] [--max-seconds SECONDS]
```

Arguments:

- `PATH` (positional, optional): directory to analyze. Defaults to `.` (current directory).
- `-o, --output-dir`: where to write `data.json`. By default it is written into `PATH`.
- `-i, --ignore`: directory name to ignore (can be passed multiple times). Defaults include:
	- `.git`, `.venv`, `bin`, `__pycache__`, `.ipynb_checkpoints`
- `--max-seconds`: approximate time budget (in seconds) for computing folder sizes.
	- default: `15.0`
	- after the budget is used up, the tool stops computing precise sizes and continues building the tree, using `None` (rendered as size 0) for remaining nodes.
	- set to `0` to disable the limit and compute all sizes.

## How the visualization works

The viewer lives in [index.html](index.html). It assumes:

- `index.html` and `data.json` are in the same directory
- a simple HTTP server is serving that directory (e.g. `python -m http.server 8000`)

At a high level:

1. `index.html` fetches `data.json`:
	 ```js
	 const JSON_PATH = "data.json";
	 const raw = await fetch(JSON_PATH).then(r => r.json());
	 ```
2. It converts the JSON into a D3 hierarchy (`d3.hierarchy(raw)`) and applies `d3.tree` to compute positions.
3. Nodes are rendered as circles; folders are one color, files another.
4. Labels use the short `name` (file or folder name), while tooltips show both name and full path, plus formatted size.
5. Clicking a folder expands/collapses its children; hovering shows size information.

The JSON schema roughly matches what `networkx.readwrite.json_graph.tree_data` produces, with extra attributes:

- each node has
	- `id`: full absolute path (unique)
	- `name`: basename shown in the UI
	- `type`: `"folder"` or `"file"`
	- `size_bytes`: integer bytes, or `None` if not computed within the time budget
	- `children`: list of child nodes (folders/files)

## Library usage (Python API)

You can also use the functionality programmatically from Python:

```python
from dir_to_graph import build_tree_json, write_tree_json

tree = build_tree_json("/path/to/dir", max_seconds=10)
print(tree["name"], tree["children"][0]["name"])

out_path = write_tree_json("/path/to/dir", output_dir=".", filename="data.json")
print("wrote", out_path)
```

This is useful if you want to embed the directory graph in another application or run it from a notebook.

## Notes & limitations

- Very large directories can still take noticeable time, especially if `--max-seconds 0` is used.
- Size calculation skips files that cannot be read (`OSError` is ignored).
- The project is experimental; APIs and output format may change.

Contributions and ideas for new visualizations are welcome.

## Future Ideas

- I am developing an LLM to be able to ask interactively regarding the organization of the folders and files, and potentially their contents.
