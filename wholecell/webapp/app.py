"""wcEcoli Web UI — Dash application factory."""

from __future__ import annotations

import os

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from wholecell.webapp.jobs import DB_FILENAME, JobManager


def create_app(out_path: str = None, wcecoli_root: str = None,
		docker_image: str = 'wcm-code') -> dash.Dash:
	"""Create and configure the Dash application.

	Args:
		out_path: Path to the 'out/' directory with simulation results.
		wcecoli_root: Path to the wcEcoli repository root.
		docker_image: Docker image name for running simulations.
	"""

	if wcecoli_root is None:
		wcecoli_root = os.path.dirname(os.path.dirname(
			os.path.dirname(os.path.abspath(__file__))))
	if out_path is None:
		out_path = os.path.join(wcecoli_root, 'out')

	# Job manager
	db_path = os.path.join(wcecoli_root, DB_FILENAME)
	job_manager = JobManager(db_path, wcecoli_root, docker_image=docker_image)

	app = dash.Dash(
		__name__,
		suppress_callback_exceptions=True,
		title='wcEcoli Web UI',
		assets_folder=os.path.join(os.path.dirname(__file__), 'assets'),
	)

	# Import tabs
	from wholecell.webapp.tabs import configure, explore, inspect_data, runs

	# Build all tab layouts upfront so Dash registers every component ID
	# in the initial layout. Tabs are shown/hidden via CSS display property.
	tab_ids = ['inspect', 'explore', 'configure', 'runs']
	tab_contents = {
		'inspect': inspect_data.layout(out_path),
		'explore': explore.layout(out_path),
		'configure': configure.layout(),
		'runs': runs.layout(),
	}

	app.layout = html.Div([
		# WIP banner
		html.Div('🚧 Work in Progress — experimental, not for production use 🚧',
			className='wip-banner'),

		# Header
		html.Div(className='app-header', children=[
			html.H2('wcEcoli'),
			html.Span('Whole-Cell E. coli Simulation', className='subtitle'),
		]),

		# Tab bar
		dcc.Tabs(
			id='main-tabs',
			value='inspect',
			className='tab-bar',
			content_style={'display': 'none'},
			children=[
				dcc.Tab(label='Inspect Data', value='inspect', className='tab', selected_className='tab--selected'),
				dcc.Tab(label='Explore Plots', value='explore', className='tab', selected_className='tab--selected'),
				dcc.Tab(label='Configure', value='configure', className='tab', selected_className='tab--selected'),
				dcc.Tab(label='Run Status', value='runs', className='tab', selected_className='tab--selected'),
			],
		),

		# Tab panels — all rendered, one visible at a time
		*[html.Div(
			tab_contents[tid],
			id=f'tab-panel-{tid}',
			className='tab-content',
			style={'display': 'block' if tid == 'inspect' else 'none'},
		) for tid in tab_ids],

		# Footer
		html.Footer(className='app-footer', children=[
			html.Div([
				'Based on the ',
				html.A('wcEcoli whole-cell model',
					href='https://github.com/CovertLab/wcEcoli', target='_blank'),
				' by the ',
				html.A('Covert Lab at Stanford University',
					href='https://www.covert.stanford.edu/', target='_blank'),
				'. Licensed under the ',
				html.A('MIT Licence',
					href='https://github.com/CovertLab/wcEcoli/blob/master/LICENSE.md',
					target='_blank'),
				'.',
			]),
			html.Div([
				'Web UI: ',
				html.A('stevehaigh/wcEcoli-webapp',
					href='https://github.com/stevehaigh/wcEcoli-webapp', target='_blank'),
				' · Built with AI assistance.',
			]),
			html.Div(
				'This is experimental software and should not be relied upon '
				'for research conclusions.',
				className='footer-disclaimer'),
		]),
	])

	# Register tab callbacks
	inspect_data.register_callbacks(app, out_path)
	explore.register_callbacks(app, out_path)
	configure.register_callbacks(app, on_submit=lambda cfg: _submit_job(job_manager, cfg))
	runs.register_callbacks(app, job_manager)

	@app.callback(
		[Output(f'tab-panel-{tid}', 'style') for tid in tab_ids],
		Input('main-tabs', 'value'),
	)
	def render_tab(tab):
		return [
			{'display': 'block'} if tid == tab else {'display': 'none'}
			for tid in tab_ids
		]

	return app


def _submit_job(job_manager: JobManager, config: dict) -> str:
	"""Submit a job and return a status message."""

	job_id = job_manager.submit(config)
	return f'Job #{job_id} submitted! Switch to Run Status tab to monitor progress.'
