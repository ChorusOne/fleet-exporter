#!/usr/bin/env python3
"""
Fleet exporter is a script which periodically checks
host status in FleetDM API and reports compliance status
for each host.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import typing

from aiohttp import client, web
from prometheus_async import aio
from prometheus_client import Gauge


logger = logging.getLogger(__name__)


arg_parser = argparse.ArgumentParser(prog="Fleet DM policy compliance metrics")
arg_parser.add_argument(
    "-e",
    "--fleetdm-api-endpoint",
    default=os.environ.get("FLEET_API_ENDPOINT", "http://127.0.0.1:8080"),
)
arg_parser.add_argument(
    "-A", "--fleetdm-api-token", default=os.environ.get("FLEET_API_TOKEN", "")
)
arg_parser.add_argument(
    "-t",
    "--scrape-period-ms",
    default=os.environ.get("FLEET_SCRAPE_PERIOD_MS", "60000"),
)


arg_parser.add_argument("-H", "--host", default="0.0.0.0", help="Listen on this host.")
arg_parser.add_argument(
    "-P", "--port", type=str, default=19339, help="Listen on this port."
)


list_hosts = Gauge(
    name="fleet_exporter_list_host",
    documentation="Status of listing host via an API",
    labelnames=["endpoint", "status"],
)
http_request = Gauge(
    name="fleet_exporter_http_request",
    documentation="Status of individual HTTP requests to fleet API",
    labelnames=["endpoint", "path", "status_code"],
)
compliance_status = Gauge(
    name="fleet_exporter_compliance_status",
    documentation="Policy compliance status for individual hosts",
    labelnames=[
        "endpoint",
        "primary_ip",
        "public_ip",
        "hostname",
        "policy",
        "platform",
        "response",
    ],
)


async def retrieve_and_expose_compliance_facts(
    endpoint: str, session: client.ClientSession
) -> None:
    """Runs a single iteration of FleetDM API retrieval, renews metric values"""
    now = int(time.time())

    async def retrieve(path: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
        response = await session.get(path)
        expose(http_request, path, str(response.status))
        if response.status != 200:
            logger.error(
                f"Non-200 response from fleet API on path {path}: {response:?}"
            )
            return None
        return await response.json()  # type: ignore

    def expose(_metric: Gauge, *labels: str) -> None:
        """Expose given metric of put_get_del set."""
        _metric.labels(endpoint, *labels).set(now)

    hosts = await retrieve("/api/v1/fleet/hosts")
    if not hosts:
        expose(list_hosts, "failure")
        return

    expose(list_hosts, "success")

    host_infos = await asyncio.gather(
        *[retrieve(f"/api/v1/fleet/hosts/{host['id']}") for host in hosts["hosts"]]
    )

    for info in host_infos:
        host = info["host"]
        for policy in host["policies"]:
            expose(
                compliance_status,
                host["primary_ip"],
                host["public_ip"],
                host["hostname"],
                policy["name"],
                policy["platform"],
                policy["response"],
            )


def check(
    loop: asyncio.AbstractEventLoop,
    api_endpoint: str,
    api_token: str,
    period: float,
) -> None:
    """Configure and start endless FleetDM API checking loop."""

    async def checker_loop() -> None:
        """Infinite loop that spawns checker tasks."""
        while True:
            session = client.ClientSession(
                base_url=api_endpoint,
                headers={
                    "Authorization": f"Bearer {api_token}",
                },
            )
            await retrieve_and_expose_compliance_facts(
                api_endpoint,
                session=session,
            )
            await asyncio.sleep(period)

    loop.create_task(checker_loop())
    logger.info(f"Started loop for API endpoint {api_endpoint}")


def main() -> None:
    """Main function"""
    args = arg_parser.parse_args()
    token = args.fleetdm_api_token
    if not token:
        logger.error("Need to have fleet DM API token provided")
        sys.exit(2)
    try:
        period_ms = int(args.scrape_period_ms)
    except ValueError:
        logger.error("Scrape period is not a valid integer millisecond value")
        sys.exit(2)
    endpoint = args.fleetdm_api_endpoint
    loop = asyncio.get_event_loop()

    async def app_factory() -> web.Application:
        check(
            loop=loop,
            api_endpoint=endpoint,
            api_token=token,
            period=period_ms / 1000.0,
        )
        app = web.Application()
        app.router.add_get("/metrics", aio.web.server_stats)
        return app

    web.run_app(app=app_factory(), host=args.host, port=args.port, loop=loop)


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    )
    main()
