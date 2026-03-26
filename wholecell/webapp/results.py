"""Scan simulation output directories and read listener data."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from wcecoli_io.tablereader import DoesNotExistError, TableReader


# Patterns for directory structure
VARIANT_PATTERN = re.compile(r'.+_\d{6}')
SEED_PATTERN = re.compile(r'\d{6}')
GENERATION_PATTERN = re.compile(r'generation_\d{6}')
DAUGHTER_PATTERN = re.compile(r'\d{6}')


def find_sim_dirs(out_path: str) -> List[str]:
	"""Find top-level simulation output directories (those containing
	variant subdirectories or a kb/ folder)."""

	sim_dirs = []
	if not os.path.isdir(out_path):
		return sim_dirs

	for name in sorted(os.listdir(out_path)):
		candidate = os.path.join(out_path, name)
		if not os.path.isdir(candidate):
			continue
		# A sim dir has variant subdirs or a kb/ folder
		if os.path.isdir(os.path.join(candidate, 'kb')):
			sim_dirs.append(candidate)
			continue
		for sub in os.listdir(candidate):
			if VARIANT_PATTERN.fullmatch(sub) or sub.startswith('wildtype_'):
				sim_dirs.append(candidate)
				break

	return sim_dirs


def find_variants(sim_dir: str) -> List[str]:
	"""Find variant subdirectories within a simulation output directory."""

	variants = []
	if not os.path.isdir(sim_dir):
		return variants

	for name in sorted(os.listdir(sim_dir)):
		path = os.path.join(sim_dir, name)
		if os.path.isdir(path) and (
				VARIANT_PATTERN.fullmatch(name) or name.startswith('wildtype_')):
			variants.append(name)
	return variants


def find_cells(sim_dir: str, variant: str) -> List[Dict[str, str]]:
	"""Find all cell simulation directories for a given variant.

	Returns a list of dicts with keys: seed, generation, daughter, simout_path.
	"""

	cells = []
	variant_dir = os.path.join(sim_dir, variant)
	if not os.path.isdir(variant_dir):
		return cells

	for seed in sorted(os.listdir(variant_dir)):
		if not SEED_PATTERN.fullmatch(seed):
			continue
		seed_dir = os.path.join(variant_dir, seed)
		if not os.path.isdir(seed_dir):
			continue

		for gen in sorted(os.listdir(seed_dir)):
			if not GENERATION_PATTERN.fullmatch(gen):
				continue
			gen_dir = os.path.join(seed_dir, gen)
			if not os.path.isdir(gen_dir):
				continue

			for daughter in sorted(os.listdir(gen_dir)):
				if not DAUGHTER_PATTERN.fullmatch(daughter):
					continue
				simout = os.path.join(gen_dir, daughter, 'simOut')
				if os.path.isdir(simout):
					cells.append({
						'seed': seed,
						'generation': gen,
						'daughter': daughter,
						'simout_path': simout,
					})
	return cells


def find_listeners(simout_path: str) -> List[str]:
	"""List available listeners in a simOut directory."""

	listeners = []
	if not os.path.isdir(simout_path):
		return listeners

	for name in sorted(os.listdir(simout_path)):
		listener_dir = os.path.join(simout_path, name)
		if os.path.isdir(listener_dir) and name not in ('shell.log',):
			listeners.append(name)
	return listeners


def find_columns(simout_path: str, listener: str) -> List[str]:
	"""List available columns for a listener."""

	columns = []
	listener_dir = os.path.join(simout_path, listener)
	if not os.path.isdir(listener_dir):
		return columns

	for name in sorted(os.listdir(listener_dir)):
		# Skip metadata files
		if '.' not in name:
			columns.append(name)
	return columns


def load_column(
		simout_path: str,
		listener: str,
		column: str,
		) -> Tuple[np.ndarray, List[str]]:
	"""Load a data column from a listener.

	Returns:
		data: 2D array (n_timepoints, m_series)
		labels: label for each series
	"""

	reader = TableReader(os.path.join(simout_path, listener))
	data = reader.readColumn(column, squeeze=False)

	# Read subcolumn labels if available
	try:
		subcolumns = reader.readAttribute('subcolumns')
	except DoesNotExistError:
		subcolumns = {}

	if column in subcolumns:
		labels = list(reader.readAttribute(subcolumns[column]))
	else:
		labels = [str(i) for i in range(data.shape[1])]

	return data, labels


def load_time(simout_path: str) -> Optional[np.ndarray]:
	"""Load the time column from the Main listener, if available."""

	main_dir = os.path.join(simout_path, 'Main')
	if not os.path.isdir(main_dir):
		return None
	try:
		reader = TableReader(main_dir)
		return reader.readColumn('time').flatten()
	except (DoesNotExistError, OSError, ValueError):
		return None


def find_plot_images(sim_dir: str, variant: str) -> List[Dict[str, str]]:
	"""Find analysis plot images for a variant.

	Searches plotOut/ directories for PNG files.
	Returns list of dicts with keys: name, path, cell_label.
	"""

	images = []
	cells = find_cells(sim_dir, variant)
	for cell in cells:
		plotout = cell['simout_path'].replace('simOut', 'plotOut')
		lowres = os.path.join(plotout, 'low_res_plots')

		# Prefer low_res_plots/, fall back to plotOut/
		img_dir = lowres if os.path.isdir(lowres) else plotout
		if not os.path.isdir(img_dir):
			continue

		cell_label = f"s{cell['seed']}/{cell['generation']}"
		for name in sorted(os.listdir(img_dir)):
			if name.lower().endswith(('.png', '.svg')):
				images.append({
					'name': os.path.splitext(name)[0],
					'path': os.path.join(img_dir, name),
					'cell_label': cell_label,
				})
	return images
