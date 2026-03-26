"""Inspect tab — interactive listener data browser."""

from __future__ import annotations

from typing import List, Tuple

import dash
from dash import dcc, html, ALL
from dash.dependencies import Input, Output, State
import numpy as np
import plotly.graph_objs as go

from wholecell.webapp import results


def make_run_options(out_path: str) -> List[dict]:
	"""Build dropdown options from available simulation directories."""

	options = []
	for sim_dir in results.find_sim_dirs(out_path):
		for variant in results.find_variants(sim_dir):
			cells = results.find_cells(sim_dir, variant)
			if cells:
				label = f"{variant} ({len(cells)} cell{'s' if len(cells) > 1 else ''})"
				# Encode as sim_dir + variant separated by |
				value = f"{sim_dir}|{variant}"
				options.append({'label': label, 'value': value})
	return options


def parse_run_value(value: str) -> Tuple[str, str]:
	"""Parse a run dropdown value into (sim_dir, variant)."""
	parts = value.split('|', 1)
	if len(parts) != 2:
		raise ValueError(f'Invalid run value (expected sim_dir|variant): {value!r}')
	return parts[0], parts[1]


def layout(out_path: str) -> html.Div:
	"""Create the Inspect tab layout."""

	run_options = make_run_options(out_path)

	return html.Div(children=[
		html.Div(className='grid-3', style={'marginBottom': '15px'}, children=[
			html.Div([
				html.Label('Run'),
				dcc.Dropdown(
					id='inspect-run',
					options=run_options,
					value=run_options[0]['value'] if run_options else None,
				),
			]),
			html.Div([
				html.Label('Listener'),
				dcc.Dropdown(id='inspect-listener'),
			]),
			html.Div([
				html.Label('Column'),
				dcc.Dropdown(id='inspect-column'),
			]),
		]),

		html.Div(style={'marginBottom': '15px', 'display': 'flex', 'gap': '20px', 'alignItems': 'center'}, children=[
			html.Label('Transform:'),
			dcc.Checklist(
				id='inspect-transform',
				options=[
					{'label': ' Normalize to t=0', 'value': 'normalize'},
					{'label': ' Log scale', 'value': 'log'},
				],
				value=[],
				inline=True,
				style={'display': 'flex', 'gap': '15px'},
			),
		]),

		dcc.Graph(
			id='inspect-graph',
			style={'height': '550px'},
			config={'displayModeBar': True, 'scrollZoom': True},
		),

		# Overlay controls
		html.Div(style={'marginTop': '15px', 'padding': '10px', 'background': '#f0f0f0', 'borderRadius': '5px'}, children=[
			html.Label('Overlay traces from other runs:', style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
			html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr auto', 'gap': '10px', 'alignItems': 'end'}, children=[
				dcc.Dropdown(
					id='inspect-overlay-run',
					options=run_options,
					placeholder='Select run...',
				),
				dcc.Dropdown(id='inspect-overlay-listener', placeholder='Listener...'),
				dcc.Dropdown(id='inspect-overlay-column', placeholder='Column...'),
				html.Button('Add Trace', id='inspect-add-trace', n_clicks=0,
					style={'padding': '8px 16px', 'cursor': 'pointer'}),
			]),

			# Active overlay list
			html.Div(id='inspect-overlay-list', style={'marginTop': '8px'}),
		]),

		# Hidden stores
		dcc.Store(id='inspect-overlay-traces', data=[]),
	])


def _render_overlay_list(traces: list) -> list:
	"""Render the list of active overlay traces with remove buttons."""
	if not traces:
		return []
	items = []
	for i, t in enumerate(traces):
		run_label = t['run'].split('|', 1)[-1] if '|' in t['run'] else t['run']
		label = f"{run_label} / {t['listener']} / {t['column']}"
		items.append(html.Div(
			style={'display': 'inline-flex', 'alignItems': 'center', 'gap': '4px',
				'background': '#fff', 'border': '1px solid #d0d7de', 'borderRadius': '12px',
				'padding': '2px 8px 2px 10px', 'fontSize': '12px', 'marginRight': '6px',
				'marginTop': '4px'},
			children=[
				html.Span(label, style={'color': '#1f2328'}),
				html.Button('x',
					id={'type': 'remove-overlay-btn', 'index': i},
					style={'background': 'none', 'border': 'none', 'cursor': 'pointer',
						'color': '#cf222e', 'fontWeight': 'bold', 'fontSize': '13px',
						'padding': '0 2px', 'lineHeight': '1'}),
			],
		))
	return [
		html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center'}, children=[
			*items,
			html.Button('Clear all', id='inspect-clear-overlays', n_clicks=0,
				style={'fontSize': '11px', 'padding': '2px 8px', 'cursor': 'pointer',
					'marginLeft': '8px', 'marginTop': '4px'}),
		]),
	]


def register_callbacks(app: dash.Dash, out_path: str) -> None:
	"""Register all Inspect tab callbacks."""

	@app.callback(
		Output('inspect-listener', 'options'),
		Output('inspect-listener', 'value'),
		Input('inspect-run', 'value'),
	)
	def update_listeners(run_value):
		if not run_value:
			return [], None
		sim_dir, variant = parse_run_value(run_value)
		cells = results.find_cells(sim_dir, variant)
		if not cells:
			return [], None
		listeners = results.find_listeners(cells[0]['simout_path'])
		options = [{'label': l, 'value': l} for l in listeners]
		# Default to Mass if available
		default = 'Mass' if 'Mass' in listeners else (listeners[0] if listeners else None)
		return options, default

	@app.callback(
		Output('inspect-column', 'options'),
		Output('inspect-column', 'value'),
		Input('inspect-listener', 'value'),
		State('inspect-run', 'value'),
	)
	def update_columns(listener, run_value):
		if not listener or not run_value:
			return [], None
		sim_dir, variant = parse_run_value(run_value)
		cells = results.find_cells(sim_dir, variant)
		if not cells:
			return [], None
		columns = results.find_columns(cells[0]['simout_path'], listener)
		options = [{'label': c, 'value': c} for c in columns]
		# Default to dryMass for Mass listener, else first column
		if listener == 'Mass' and 'dryMass' in columns:
			default = 'dryMass'
		elif listener == 'Main' and 'time' in columns:
			default = 'time'
		else:
			default = columns[0] if columns else None
		return options, default

	# Same cascading logic for overlay dropdowns
	@app.callback(
		Output('inspect-overlay-listener', 'options'),
		Output('inspect-overlay-listener', 'value'),
		Input('inspect-overlay-run', 'value'),
	)
	def update_overlay_listeners(run_value):
		if not run_value:
			return [], None
		sim_dir, variant = parse_run_value(run_value)
		cells = results.find_cells(sim_dir, variant)
		if not cells:
			return [], None
		listeners = results.find_listeners(cells[0]['simout_path'])
		options = [{'label': l, 'value': l} for l in listeners]
		return options, None

	@app.callback(
		Output('inspect-overlay-column', 'options'),
		Output('inspect-overlay-column', 'value'),
		Input('inspect-overlay-listener', 'value'),
		State('inspect-overlay-run', 'value'),
	)
	def update_overlay_columns(listener, run_value):
		if not listener or not run_value:
			return [], None
		sim_dir, variant = parse_run_value(run_value)
		cells = results.find_cells(sim_dir, variant)
		if not cells:
			return [], None
		columns = results.find_columns(cells[0]['simout_path'], listener)
		options = [{'label': c, 'value': c} for c in columns]
		return options, None

	@app.callback(
		Output('inspect-overlay-traces', 'data'),
		Input('inspect-add-trace', 'n_clicks'),
		Input({'type': 'remove-overlay-btn', 'index': ALL}, 'n_clicks'),
		Input('inspect-clear-overlays', 'n_clicks'),
		State('inspect-overlay-run', 'value'),
		State('inspect-overlay-listener', 'value'),
		State('inspect-overlay-column', 'value'),
		State('inspect-overlay-traces', 'data'),
		prevent_initial_call=True,
	)
	def modify_overlay_traces(add_clicks, remove_clicks_list, clear_clicks,
			run_value, listener, column, existing_traces):
		from dash import ctx
		triggered = ctx.triggered_id
		traces = list(existing_traces or [])

		# Clear all
		if triggered == 'inspect-clear-overlays':
			return []

		# Remove specific trace
		if isinstance(triggered, dict) and triggered.get('type') == 'remove-overlay-btn':
			idx = triggered['index']
			if 0 <= idx < len(traces):
				traces.pop(idx)
			return traces

		# Add new trace
		if triggered == 'inspect-add-trace' and all([run_value, listener, column]):
			new_trace = {
				'run': run_value,
				'listener': listener,
				'column': column,
			}
			if new_trace not in traces:
				traces.append(new_trace)

		return traces

	@app.callback(
		Output('inspect-overlay-list', 'children'),
		Input('inspect-overlay-traces', 'data'),
	)
	def render_overlay_list(traces):
		return _render_overlay_list(traces or [])

	@app.callback(
		Output('inspect-graph', 'figure'),
		Input('inspect-column', 'value'),
		Input('inspect-transform', 'value'),
		Input('inspect-overlay-traces', 'data'),
		State('inspect-run', 'value'),
		State('inspect-listener', 'value'),
	)
	def update_graph(column, transforms, overlay_traces, run_value, listener):
		if not all([column, run_value, listener]):
			return go.Figure()

		transforms = transforms or []
		fig = go.Figure()

		# Load primary trace
		_add_traces_to_fig(fig, run_value, listener, column, transforms,
			is_primary=True)

		# Load overlay traces
		for trace_info in (overlay_traces or []):
			_add_traces_to_fig(
				fig,
				trace_info['run'],
				trace_info['listener'],
				trace_info['column'],
				transforms,
				is_primary=False,
			)

		fig.update_layout(
			xaxis_title='Time (s)',
			yaxis_title=f'{listener} / {column}',
			hovermode='closest',
			template='plotly_white',
			legend=dict(orientation='h', yanchor='bottom', y=1.02),
		)
		if 'log' in transforms:
			fig.update_yaxis(type='log')

		return fig


def _add_traces_to_fig(
		fig: go.Figure,
		run_value: str,
		listener: str,
		column: str,
		transforms: list,
		is_primary: bool = True,
		) -> None:
	"""Load data and add traces to a Plotly figure."""

	try:
		sim_dir, variant = parse_run_value(run_value)
		cells = results.find_cells(sim_dir, variant)
		if not cells:
			return

		simout = cells[0]['simout_path']
		time = results.load_time(simout)
		data, labels = results.load_column(simout, listener, column)
	except Exception:
		return

	if 'normalize' in transforms and data.shape[0] > 0:
		norm_row = data[0, :]
		norm_row = np.where(norm_row == 0, 1, norm_row)
		data = data / norm_row

	prefix = '' if is_primary else f'{variant} · '
	dash_style = None if is_primary else 'dash'
	x_vals = time if time is not None else np.arange(data.shape[0])
	n_series = min(len(labels), data.shape[1])

	# For columns with many series (>20), just plot the sum
	if n_series > 20:
		fig.add_trace(go.Scatter(
			x=x_vals,
			y=data.sum(axis=1),
			name=f'{prefix}{column} (sum of {n_series})',
			line=dict(dash=dash_style),
			mode='lines+markers',
		))
	else:
		for i in range(n_series):
			name = f'{prefix}{labels[i]}' if n_series > 1 else f'{prefix}{column}'
			fig.add_trace(go.Scatter(
				x=x_vals,
				y=data[:, i],
				name=name,
				line=dict(dash=dash_style),
				mode='lines+markers',
			))
