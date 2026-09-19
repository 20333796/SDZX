ARG IMAGE_PREFIX=docker.io/library/
FROM ${IMAGE_PREFIX}python:3.12-slim

WORKDIR /workspace
COPY scripts/import_geochat_knowledge.py scripts/import_geochat_knowledge.py
COPY apps/web/src/config/mentorDirections.json apps/web/src/config/mentorDirections.json
COPY apps/web/src/config/mentorGraph.ts apps/web/src/config/mentorGraph.ts
RUN pip install --no-cache-dir "PyJWT==2.14.0" "requests==2.32.5"

ENTRYPOINT ["python", "scripts/import_geochat_knowledge.py"]
