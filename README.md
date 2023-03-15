fleet-exporter
===============

Exports information regarding policy compliance for [FleetDM](https://github.com/fleetdm/fleet/)-enrolled hosts,
in form of Prometheus metrics.

Installation
-------------
```bash
python3 -m venv venv
python3 -m pip -r ./requirements.txt
```

Usage
-----
```bash
export FLEET_API_ENDPOINT=https://fleet.example.com:1337/  # Base URL for fleet server
export FLEET_API_TOKEN=XYZ                                 # Static API token (of API-only user)
export FLEET_SCRAPE_PERIOD_MS=60000                        # Scrape delay in milliseconds

venv/bin/python3 fleet-exporter.py --host 0.0.0.0 --port 8080
```

Available metrics
------------------
All metrics are gauges, where the value is timestamp when the particular
fact was spotted.

- `fleet_exporter_list_host` -- status of host discovery by exporter via Fleet API

  Labels:
    - `endpoint` -- fleet API endpoint used
    - `status` -- "success" or "failure"


- `fleet_exporter_http_request` -- status of distinct HTTP requests via Fleet API

  Labels:
    - `endpoint` -- fleet API endpoint used
    - `path` -- request URI path
    - `status` -- response status code


- `fleet_exporter_compliance_status`

  Labels:
    - `endpoint` -- fleet API endpoint used
    - `primary_ip` -- primary IP of a host where policy was evaluated
    - `public_ip` -- public IP of a host where policy was evaluated
    - `hostname` -- hostname for this host
    - `policy` -- name of the policy which was evaluated
    - `response` -- evaluation response (typically "pass" or "fail")
    - `platform` -- platform, one of "linux", "windows", "darwin"
