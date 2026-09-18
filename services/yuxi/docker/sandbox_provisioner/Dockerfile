ARG IMAGE_PREFIX=docker.io/library/
FROM ${IMAGE_PREFIX}python:3.13-slim

WORKDIR /app
ARG INSTALL_KUBERNETES_SANDBOX=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
COPY requirements-kubernetes.txt /app/requirements-kubernetes.txt
RUN pip install --no-cache-dir -r /app/requirements.txt --index https://pypi.tuna.tsinghua.edu.cn/simple \
    && if [ "$INSTALL_KUBERNETES_SANDBOX" = "true" ]; then pip install --no-cache-dir -r /app/requirements-kubernetes.txt --index https://pypi.tuna.tsinghua.edu.cn/simple; fi

COPY app.py /app/app.py

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
