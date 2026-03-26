"""Configure tab — simulation setup form."""

from __future__ import annotations

import json
import os

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

# Load model config from config/wcecoli.json (repo root)
_CONFIG_PATH = os.path.join(
	os.path.dirname(__file__), '..', '..', '..', 'config', 'wcecoli.json')

with open(os.path.normpath(_CONFIG_PATH)) as _f:
	_MODEL_CONFIG = json.load(_f)

VARIANT_NAMES = _MODEL_CONFIG['variants']
TOGGLES = _MODEL_CONFIG['toggles']   # list of dicts: name, label, default, hint
PRESETS = _MODEL_CONFIG['presets']   # list of dicts: id, label, description, config


def layout() -> html.Div:
	"""Create the Configure tab layout."""

	default_toggles = [t['name'] for t in TOGGLES if t['default']]

	preset_buttons = [
		html.Button(
			p['label'],
			id=p['id'],
			n_clicks=0,
			className='btn-preset',
			title=p['description'],
		)
		for p in PRESETS
	]

	return html.Div(style={'maxWidth': '700px'}, children=[

		# Presets section
		html.Div(style={'marginBottom': '24px'}, children=[
			html.Label('Quick start presets'),
			html.P(
				'Click a preset to fill in the form below, then adjust as needed and click Run Simulation.',
				style={'color': '#57606a', 'fontSize': '13px', 'margin': '4px 0 10px 0'},
			),
			html.Div(preset_buttons, style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px'}),
			html.Div(id='preset-description', style={
				'marginTop': '8px', 'fontSize': '13px', 'color': '#57606a',
				'fontStyle': 'italic', 'minHeight': '18px',
			}),
		]),

		html.Hr(style={'border': 'none', 'borderTop': '1px solid #d0d7de', 'marginBottom': '20px'}),

		html.Div(className='grid-2', style={'marginBottom': '20px'}, children=[
			html.Div([
				html.Label('Variant type'),
				dcc.Dropdown(
					id='config-variant',
					options=[{'label': v, 'value': v} for v in VARIANT_NAMES],
					value='wildtype',
				),
			]),
			html.Div([
				html.Label('Variant index range'),
				html.Div(style={'display': 'flex', 'gap': '5px', 'alignItems': 'center'}, children=[
					dcc.Input(id='config-variant-first', type='number', value=0, min=0,
						style={'width': '60px'}),
					html.Span('to'),
					dcc.Input(id='config-variant-last', type='number', value=0, min=0,
						style={'width': '60px'}),
				]),
			]),
		]),

		html.Div(className='grid-3', style={'marginBottom': '20px'}, children=[
			html.Div([
				html.Label('Generations'),
				dcc.Input(id='config-generations', type='number', value=1, min=1,
					style={'width': '100%'}),
			]),
			html.Div([
				html.Label('Seeds'),
				dcc.Input(id='config-seeds', type='number', value=1, min=1,
					style={'width': '100%'}),
			]),
			html.Div([
				html.Label('Seed start'),
				dcc.Input(id='config-seed-start', type='number', value=0, min=0,
					style={'width': '100%'}),
			]),
		]),

		html.Div(style={'marginBottom': '20px'}, children=[
			html.Label('Regulation toggles', style={'marginBottom': '8px'}),
			dcc.Checklist(
				id='config-toggles',
				options=[
					{
						'label': html.Span([
							f" {t['label']} ",
							html.Span('ℹ', className='toggle-hint', title=t['hint']),
						]),
						'value': t['name'],
					}
					for t in TOGGLES
				],
				value=default_toggles,
				className='grid-2',
				style={'gap': '4px'},
			),
		]),

		html.Div(style={'marginBottom': '20px'}, children=[
			html.Label('Description'),
			dcc.Input(
				id='config-description', type='text',
				placeholder='Brief description of this run...',
				style={'width': '100%'},
			),
		]),

		html.Button(
			'Run Simulation',
			id='config-run-button',
			n_clicks=0,
			className='btn-primary',
		),
		html.Div(id='config-status', style={'marginTop': '10px'}),
	])


def register_callbacks(app: dash.Dash, on_submit) -> None:
	"""Register Configure tab callbacks.

	Args:
		on_submit: callable(config_dict) that submits a job.
			Returns a status message string.
	"""

	preset_ids = [p['id'] for p in PRESETS]
	preset_lookup = {p['id']: p for p in PRESETS}

	@app.callback(
		Output('config-variant', 'value'),
		Output('config-variant-first', 'value'),
		Output('config-variant-last', 'value'),
		Output('config-generations', 'value'),
		Output('config-seeds', 'value'),
		Output('config-seed-start', 'value'),
		Output('config-description', 'value'),
		Output('preset-description', 'children'),
		[Input(pid, 'n_clicks') for pid in preset_ids],
		prevent_initial_call=True,
	)
	def apply_preset(*args):
		from dash import ctx
		triggered = ctx.triggered_id
		if not triggered or triggered not in preset_lookup:
			raise dash.exceptions.PreventUpdate
		p = preset_lookup[triggered]['config']
		desc = preset_lookup[triggered]['description']
		return (
			p['variant'], p['variant_first'], p['variant_last'],
			p['generations'], p['seeds'], p['seed_start'],
			p['description'], desc,
		)

	@app.callback(
		Output('config-status', 'children'),
		Input('config-run-button', 'n_clicks'),
		State('config-variant', 'value'),
		State('config-variant-first', 'value'),
		State('config-variant-last', 'value'),
		State('config-generations', 'value'),
		State('config-seeds', 'value'),
		State('config-seed-start', 'value'),
		State('config-toggles', 'value'),
		State('config-description', 'value'),
		prevent_initial_call=True,
	)
	def submit_run(n_clicks, variant, first_idx, last_idx, generations,
			seeds, seed_start, toggles, description):
		if not n_clicks:
			return ''

		config = {
			'variant': variant,
			'first_variant_index': first_idx or 0,
			'last_variant_index': last_idx or 0,
			'generations': generations or 1,
			'init_sims': seeds or 1,
			'seed': seed_start or 0,
			'description': description or '',
			'toggles': {t['name']: (t['name'] in (toggles or [])) for t in TOGGLES},
		}

		msg = on_submit(config)
		return html.Div(msg, style={'color': '#2ea44f', 'fontWeight': 'bold'})
