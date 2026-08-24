FROM apache/airflow:3.3.1-python3.12

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY airflow/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Make the standalone `generator` package importable from the DAG/tasks
COPY --chown=airflow:root generator /opt/airflow/generator
RUN pip install --no-cache-dir -e /opt/airflow/generator

# Make the standalone `library_scanner` package importable from the DAG/tasks
COPY --chown=airflow:root library_scanner /opt/airflow/library_scanner
RUN pip install --no-cache-dir -e /opt/airflow/library_scanner
