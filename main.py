"""CLI entrypoint for dir_to_graph.

This module simply forwards to the package CLI so that you can run

    python main.py [path]

while developing locally, or use the installed console script when the
package is installed.
"""

from dir_to_graph.cli import main as _main


if __name__ == "__main__":
     _main()