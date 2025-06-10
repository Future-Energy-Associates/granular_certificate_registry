#!/usr/bin/env python
"""
Certificate Issuance Task that can accept optional date parameters.

Usage:
  python issuance_task.py [--from_date YYYY-MM-DD] [--to_date YYYY-MM-DD]

Arguments:
  --from_date  Optional start date in YYYY-MM-DD format. Defaults to yesterday.
  --to_date    Optional end date in YYYY-MM-DD format. Defaults to today.
"""

import argparse
import datetime
import sys

import pytz

from gc_registry.certificate.services import (
    issue_certificates_metering_integration_for_all_devices_in_date_range,
)
from gc_registry.device.meter_data.elexon.elexon import ElexonClient


def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format to a datetime object."""
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.replace(tzinfo=pytz.UTC)
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Expected format: YYYY-MM-DD")
        sys.exit(1)


def issue_for_all_generators_and_certificates_from_elexon(from_date=None, to_date=None):
    """
    Issue certificates for all generators and certificates from Elexon.
    Args:
        from_date: Optional start datetime. Defaults to yesterday at 23:00 UTC.
        to_date: Optional end datetime. Defaults to today at 00:00 UTC.
    """
    # Default to_date is today at 00:00 UTC
    if to_date is None:
        to_datetime = datetime.datetime.now(tz=pytz.UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        to_datetime = to_date

    # Default from_date is yesterday at 23:00 UTC (1 hour before midnight)
    if from_date is None:
        from_datetime = to_datetime - datetime.timedelta(days=15, hours=1)
    else:
        from_datetime = from_date

    print(f"Issuing certificates from {from_datetime} to {to_datetime}")

    metering_client = ElexonClient()

    issue_certificates_metering_integration_for_all_devices_in_date_range(
        from_datetime, to_datetime, metering_client
    )


def main():
    parser = argparse.ArgumentParser(description="Certificate Issuance Task")
    parser.add_argument(
        "--from_date", help="Start date in YYYY-MM-DD format. Defaults to yesterday."
    )
    parser.add_argument(
        "--to_date", help="End date in YYYY-MM-DD format. Defaults to today."
    )

    args = parser.parse_args()

    from_date = parse_date(args.from_date) if args.from_date else None
    to_date = parse_date(args.to_date) if args.to_date else None

    issue_for_all_generators_and_certificates_from_elexon(from_date, to_date)


if __name__ == "__main__":
    main()
