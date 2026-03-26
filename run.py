#!/usr/bin/env python
"""Entry point for the wcEcoli Web UI.

Usage:
    python run.py [--port PORT] [--out OUT_DIR] [--docker-image IMAGE]

The webapp runs simulations by shelling out to a wcEcoli Docker image.
Set WCECOLI_WEBAPP_MODE=container if running inside the wcEcoli container itself.
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
	parser = argparse.ArgumentParser(description='wcEcoli Web UI')
	parser.add_argument('--port', type=int, default=8050,
		help='Port to run the web server on (default: 8050)')
	parser.add_argument('--out', type=str, default=None,
		help='Path to simulation output directory (default: ./out/)')
	parser.add_argument('--debug', action='store_true',
		help='Enable Dash debug mode with hot reload')
	parser.add_argument('--docker-image', type=str, default='wcm-code',
		help='Docker image name for running simulations (default: wcm-code)')
	args = parser.parse_args()

	wcecoli_root = os.getcwd()
	out_path = args.out or os.path.join(wcecoli_root, 'out')

	if not os.path.isdir(out_path):
		print(f"Warning: output directory '{out_path}' does not exist.")
		print("The app will start but Inspect/Explore tabs will be empty.")

	from wholecell.webapp.app import create_app
	app = create_app(out_path=out_path, wcecoli_root=wcecoli_root,
		docker_image=args.docker_image)
	print(f"\n  wcEcoli Web UI running at http://localhost:{args.port}/\n")
	app.run(host='0.0.0.0', port=args.port, debug=args.debug)


if __name__ == '__main__':
	main()
