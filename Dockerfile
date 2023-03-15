FROM python:slim-bullseye
WORKDIR /app
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
COPY fleet-exporter.py /usr/local/bin/fleet-exporter.py
ENTRYPOINT [ "/usr/local/bin/fleet-exporter.py" ]
