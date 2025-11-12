import argparse
import asyncio
import datetime
import json
import logging
import sys
from dataclasses import asdict

from ct_moniteur import CTMoniteur


class DateTimeAwareEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects"""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def main():
    parser = argparse.ArgumentParser(
        description="Connect to Certificate Transparency logs and process certificate updates."
    )
    parser.add_argument(
        "--domains-only",
        action="store_true",
        help="Output only domain names",
    )
    parser.add_argument("--json", action="store_true", help="Format output as JSON")
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        dest="verbose",
        help="Display debug logging.",
    )

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO

    logging.basicConfig(
        format="[%(levelname)s:%(name)s] %(asctime)s - %(message)s", level=log_level
    )

    def process_certificate(entry):
        """Process each certificate entry"""
        if args.domains_only:
            if args.json:
                # Output JSON array of domains
                sys.stdout.write(json.dumps(entry.domains) + "\n")
                sys.stdout.flush()
            else:
                # Output one domain per line
                for domain in entry.domains:
                    sys.stdout.write(domain + "\n")
                sys.stdout.flush()
        elif args.json:
            # Convert entry to dict using asdict, excluding certificate object
            entry_dict = asdict(entry)
            entry_dict.pop("certificate", None)  # Remove non-serializable certificate
            sys.stdout.flush()
            sys.stdout.write(json.dumps(entry_dict, cls=DateTimeAwareEncoder) + "\n")
            sys.stdout.flush()
        else:
            # Convert timestamp from milliseconds to seconds
            timestamp = entry.timestamp / 1000.0
            payload = "{} {} - [{}]\n".format(
                "[{}]".format(datetime.datetime.fromtimestamp(timestamp).isoformat()),
                entry.source.log.url,
                ", ".join(entry.domains),
            )
            sys.stdout.write(payload)
            sys.stdout.flush()

    async def run_monitor():
        # Create monitor
        monitor = CTMoniteur(callback=process_certificate)

        try:
            # Start monitoring from current position
            await monitor.start()

            # Run indefinitely (or until Ctrl+C)
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        finally:
            await monitor.stop()

    asyncio.run(run_monitor())


if __name__ == "__main__":
    main()
