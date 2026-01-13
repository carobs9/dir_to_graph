import os
import json
import time
from typing import Iterable, Optional, Sequence

import networkx as nx
from networkx.readwrite import json_graph

# Default directory names to ignore when walking a tree
DEFAULT_IGNORES: Sequence[str] = [
    ".git",
    ".venv",
    "venv",
    "bin",
    "__pycache__",
    ".ipynb_checkpoints",
]


def get_folder_size(path: str, deadline: Optional[float] = None) -> Optional[int]:
    """Return total size in bytes of all files under path.

    This walks the directory tree rooted at ``path`` and sums file sizes.
    If ``deadline`` is provided and the current monotonic time exceeds it,
    the function aborts early and returns ``None``.
    """
    total = 0 # initialize total size counter
    for root, _dirs, files in os.walk(path): # walk through directory tree
        if deadline is not None and time.monotonic() > deadline: # skip process if deadline exceeded
            return None
        for name in files: # loop over files in provided directory
            if deadline is not None and time.monotonic() > deadline: # skip process if deadline exceeded
                return None
            full_path = os.path.join(root, name) # get full file path
            if os.path.isfile(full_path): # check if path is a file
                try:
                    total += os.path.getsize(full_path) # if so, add its size to total
                except OSError:
                    # else, ignore file
                    print(f"[WARNING] Could not access size of file: {full_path}")
                    continue
    return total


def _normalize_ignores(ignore: Optional[Iterable[str]]) -> set[str]:
    if ignore is None: # use default ignores if none provided
        return set(DEFAULT_IGNORES)
    if isinstance(ignore, str): # if single string provided, convert to set
        return {ignore}
    return set(ignore)


def build_dod(dir_of_interest: str, ignore: Optional[Iterable[str]] = None) -> dict:
    """Build a dictionary-of-dictionaries representation of a directory tree.

    The top-level keys are directory names; values are mappings from child name
    to a small metadata dict with ``type`` ("folder" or "file") and
    ``size_bytes``.
    """
    print("[INFO] Building dictionary-of-dictionaries representation. This step may take a while for large directories...")
    ignore_set = _normalize_ignores(ignore) # retrieve normalized set of directories to ignore
    dod: dict[str, dict[str, dict]] = {} # initialize dictionary of dictionaries

    for subdir, dirs, files in os.walk(dir_of_interest): # walk through provided directory tree
        dirs[:] = [d for d in dirs if d not in ignore_set] # Filter out ignored directory names *in place* so walk will skip them

        parent = os.path.basename(subdir) or subdir # retrieve name of subdir
        dod.setdefault(parent, {}) # initialize parent entry in DoD

        # Add subdirectories
        for d in dirs: # loop over subdirectories
            folder_path = os.path.join(subdir, d) # get full path of subdirectory
            folder_size = get_folder_size(folder_path) # compute size of subdirectory
            dod[parent][d] = { # add subdirectory entry in DoD
                "type": "folder", # type: folder / file
                "size_bytes": folder_size, # size in bytes
            }

        # Add files
        for file_name in files: # loop over files
            full_path = os.path.join(subdir, file_name) # get full path of file
            try:
                size = os.path.getsize(full_path) # get size of file
            except OSError:
                size = None # if error, set size to None
                print(f"[WARNING] Could not access size of file: {full_path}")
            dod[parent][file_name] = {
                "type": "file", # type: folder / file
                "size_bytes": size, # size in bytes
            }

    return dod



def build_tree_json(
    dir_of_interest: str,
    ignore: Optional[Iterable[str]] = None,
    max_seconds: Optional[float] = None,
) -> dict:
    """High-level helper: directory path -> tree-style JSON structure.

    The returned dict is compatible with ``d3.hierarchy``: it has ``id``,
    optional ``children``, and carries ``type`` / ``size_bytes`` in each node.
    A global time budget for folder size calculation can be provided via
    ``deadline``; after this budget is exhausted, further size calculations
    return ``None`` but the tree is still built.
    """
    print("[INFO] Building tree-style JSON structure. This may take a while for large directories...")
    # Build a proper tree where each node is identified by its *full path*,
    # which guarantees uniqueness and avoids accidental cycles when directory
    # names repeat (e.g. nested "dir_to_graph" folders).
    dir_of_interest = os.path.abspath(dir_of_interest) # get absolute path of directory of interest
    ignore_set = _normalize_ignores(ignore) # retrieve normalized set of directories to ignore

    if max_seconds is not None and max_seconds > 0: 
        deadline: Optional[float] = time.monotonic() + max_seconds # compute absolute deadline time
    else:
        deadline = None

    g = nx.DiGraph() # initialize directed graph

    for subdir, dirs, files in os.walk(dir_of_interest): # walk through provided directory tree
        # Skip ignored directory names
        dirs[:] = [d for d in dirs if d not in ignore_set]

        parent_path = os.path.abspath(subdir) # get absolute path of parent directory
        parent_name = os.path.basename(parent_path) or parent_path # retrieve name of parent directory

        if not g.has_node(parent_path): # if parent node not already in graph, add it
            parent_size = get_folder_size(parent_path, deadline=deadline) # compute size of parent directory
            g.add_node(
                parent_path, # node id: absolute path
                type="folder", # type: folder / file
                name=parent_name, # name: base name of directory
                size_bytes=parent_size, # size in bytes
            )

        # Add subdirectories as children
        for d in dirs: # loop over subdirectories
            child_path = os.path.abspath(os.path.join(subdir, d)) # get absolute path of subdirectory
            if not g.has_node(child_path): # if child node not already in graph, add it
                child_size = get_folder_size(child_path, deadline=deadline)
                g.add_node(
                    child_path,
                    type="folder",
                    name=d,
                    size_bytes=child_size,
                )
            g.add_edge(parent_path, child_path)

        # Add files as children
        for file_name in files:
            full_path = os.path.abspath(os.path.join(subdir, file_name))
            try:
                size = os.path.getsize(full_path)
            except OSError:
                print(f"[WARNING] Could not access size of file: {full_path}")
                size = None

            if not g.has_node(full_path):
                g.add_node(
                    full_path,
                    type="file",
                    name=file_name,
                    size_bytes=size,
                )
            g.add_edge(parent_path, full_path)

    root_id = os.path.abspath(dir_of_interest)
    if not g.has_node(root_id):
        # Should not normally happen, but keep a defensive default.
        g.add_node(root_id, type="folder", name=os.path.basename(root_id))

    # Convert to the tree-like JSON structure NetworkX provides
    tree_data = json_graph.tree_data(g, root=root_id)
    return tree_data


def write_tree_json(
    dir_of_interest: str,
    output_dir: Optional[str] = None,
    filename: str = "data.json",
    ignore: Optional[Iterable[str]] = None,
    max_seconds: Optional[float] = None,
) -> str:
    """Build tree JSON for ``dir_of_interest`` and write it to disk.

    Returns the absolute path to the written JSON file.
    """
    print("[INFO] Saving JSON file. This may take a while for large directories...")
    if output_dir is None:
        output_dir = dir_of_interest

    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    tree_data = build_tree_json(dir_of_interest, ignore=ignore, max_seconds=max_seconds)
    out_path = os.path.join(output_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, indent=2)

    return out_path
