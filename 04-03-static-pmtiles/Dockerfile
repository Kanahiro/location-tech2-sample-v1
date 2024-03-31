FROM python:3.10-slim-bullseye as base
RUN apt-get update
RUN apt-get install -y git
RUN pip3 install --no-cache-dir fastapi uvicorn[standard] git+http://github.com/developmentseed/aiopmtiles