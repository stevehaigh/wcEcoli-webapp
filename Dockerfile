# wcEcoli Web UI container.
#
# Extends a wcm-code base image (CovertLab/wcEcoli simulation environment)
# with the Dash web UI as the entrypoint.
#
# Build:
#   docker build --build-arg from=<registry>/wcm-code:latest -t wcm-webapp .
#
# Run locally (Docker mode — webapp shells out to the wcm-code image):
#   docker run --rm -p 8050:8050 -v $(pwd)/out:/wcEcoli/out wcm-webapp
#
# Then open http://localhost:8050/

ARG from=wcm-code:latest
FROM ${from}

# Copy webapp source into the wcEcoli tree so existing Python paths work
COPY wholecell/webapp/ /wcEcoli/wholecell/webapp/
COPY wcecoli_io/ /wcEcoli/wcecoli_io/
COPY config/ /wcEcoli/config/
COPY run.py /wcEcoli/run.py

# Simulations run as local subprocesses (no docker-in-docker needed)
ENV WCECOLI_WEBAPP_MODE=container

# Default to port 80 for cloud deployments; override with --port for local dev
ENV WEBAPP_PORT=80
EXPOSE 80

CMD ["sh", "-c", "python run.py --port ${WEBAPP_PORT}"]
