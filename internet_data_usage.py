#!/usr/bin/env python2

from scrapers import *

import sys
import logging
import argparse
import getpass

from influxdb import client as influxdb

"""
    TODO:
        - Confirm login was successful
        - Pull both upstream and downstream usagepint
        - Add cookie save/resume (Most time is spent authorizing)
        - Add "Days Remaining" in cycle to carrier pulls

"""

__version__ = "0.2-HEAD"
__author__ = "Andrew Klaus"
__author_email__ = "andrewklaus@gmail.com"
__copyright__ = "2015"

DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"


def main():
    logging.basicConfig()
    logger = logging.getLogger(__name__)

    # Top level parsers
    main_parser = argparse.ArgumentParser(
        description="internet_data_usage {version} Copyright (c) {copyright} {author} ({email})\n"
                    .format(version=__version__, copyright=__copyright__, author=__author__, email=__author_email__))
    subparsers = main_parser.add_subparsers(title="subcommands", help="valid subcommands")

    add_term_command(subparsers)
    add_zabbix_command(subparsers)
    add_influxdb_command(subparsers)

    args = main_parser.parse_args()

    # Run function for selected subparser
    args.func(args)


def setup_logging(verbosity):
    if verbosity > 0:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.debug("Enable logger debugging")


def get_carrier_items():
    """
        Mapping for object variables

        Key = Item to query from command line
        Val = CarrierUsageScraper variables
    """
    carrier_items = {"data_usage": "_data_usage",
                     "data_plan_total": "_data_plan_total",
                     "data_use_unit": "_data_usage_unit",
                     "plan": "_plan",
                     #"days_remaining" : "_days_remaining"
                     }

    return carrier_items


def get_carriers():
    """ Returns Dictionary to map carriers to their object """
    carriers_dict = {"telus_wireline": TelusWirelineScraper,
                     "koodo_mobile": KoodoMobileScraper}

    return carriers_dict


def add_influxdb_command(subparsers):

    parser = subparsers.add_parser("influxdb", help="all output will be sent to an influxdb database")
    parser.add_argument("username", help="Username for account access")
    parser.add_argument("password", help="Carrier password for account access")
    parser.add_argument("i_user", help="Influxdb username")
    parser.add_argument("i_pass", help="Influxdb password")
    parser.add_argument("i_host", help="Influxdb hostname")
    parser.add_argument("i_db", help="Influxdb database")
    parser.add_argument("-p", "--port", default='8086',
                        help='Port for influxdb access (default=8086)')
    parser.add_argument("-c", "--carrier", default='telus_wireline',
                        help='Carrier to query from (default=telus_wireline)',
                        choices=get_carriers().keys())
    parser.add_argument("-a", "--http_user_agent", default=DEFAULT_USER_AGENT,
                        help="Defaults to '{}'".format(DEFAULT_USER_AGENT))
    parser.add_argument("-v", "--verbose", action="store_true", default=False)

    parser.set_defaults(func=output_influxdb)


def add_zabbix_command(subparsers):
    # Arguments for zabbix output

    parser = subparsers.add_parser("zabbix", help="all output will be sent to a Zabbix server")
    parser.add_argument("username", help="Username for account access")
    parser.add_argument("password", help="Carrier password for account access")
    parser.add_argument("-i", "--item", default='data_usage',
                               help='Item to request (default=data_usage)',
                               choices=get_carrier_items().keys())
    parser.add_argument("-c", "--carrier", default='telus_wirel    ine',
                             help='Carrier to query from (default=telus_wireline)',
                             choices=get_carriers().keys())
#    parser.add_argument("-t", "--cache_time", default=0,
#                       type=int, help='Seconds to keep data cached (default=0)')
    parser.add_argument("-a", "--http_user_agent", default=DEFAULT_USER_AGENT,
                            help="Defaults to '{}'".format(DEFAULT_USER_AGENT))
    parser.add_argument("-v", "--verbose", action="store_true", default=False)

    parser.set_defaults(func=output_zabbix)


def add_term_command(subparsers):
    # Arguments for terminal-only output

    parser = subparsers.add_parser("term", help="all output will echo in a terminal")
    # term_parser.add_argument("-i", "--item", default='data_usage',
    #                         help='Item to request (default=data_usage)',
    #                         choices=get_carrier_items().keys())
    parser.add_argument("username", help="Username for account access")
    parser.add_argument("-p", "--password", default=None,
                             help="Carrier password for account access \
                             (will prompt if not specified)")
#    parser.add_argument("-t", "--cache_time", default=0,
#                       type=int, help='Seconds to keep data cached (default=0)')
    parser.add_argument("-c", "--carrier", default='telus_wireline',
                             help='Carrier to query from (default=telus_wireline)',
                             choices=get_carriers().keys())
    parser.add_argument("-a", "--http_user_agent", default=DEFAULT_USER_AGENT,
                            help="Defaults to '{}'".format(DEFAULT_USER_AGENT))
    parser.add_argument("-v", "--verbose", action="store_true", default=False)

    parser.set_defaults(func=output_term)


def output_influxdb(args):
    assert(isinstance(args, argparse.Namespace))

    logger = logging.getLogger(__name__)
    setup_logging(args.verbose)
    logger.debug("Using influxdb output")

    db = influxdb.InfluxDBClient(args.i_host, args.port, args.i_user, args.i_pass, args.i_db)

    s = scraper_get(args.carrier, args.username, args.password, args.http_user_agent, logger)
    scraper_run(s, logger)

    if not s.extended_stats:
        json_body = [
            {
             "fields":  {
                 "data_usage_total": s.data_usage_total,
                 "data_plan_total" : s.data_plan_total,
                 "plan_title" : s.plan_title,
                 "data_plan_days_left": s.data_plan_days_left,
                 "data_usage_pct": s.data_usage_pct,
              },
                "measurement": s.name + "_usage",
                'tags': {
                 "carrier": s.name,
                }
            }
        ]
    else:
        json_body = [
            {
             "fields":  {
                 "data_usage_total": s.data_usage_total,
                 "data_plan_total" : s.data_plan_total,
                 "plan_title" : s.plan_title,
                 "data_plan_days_left": s.data_plan_days_left,
                 "data_usage_pct": s.data_usage_pct,
                 "data_usage_down": s.data_usage_down,
                 "data_usage_up": s.data_usage_up
              },
                "measurement": s.name + "_usage",
                'tags': {
                 "carrier": s.name,
                }
            }
        ]

    db.write_points(json_body)


def output_zabbix(args):
    # Outputting to Zabbix selected

    assert(isinstance(args, argparse.Namespace))
    assert(args.password is not None)

    logger = logging.getLogger(__name__)
    setup_logging(args.verbose)
    logger.debug("Using zabbix output")

    s = scraper_get(args.carrier, args.username, args.password, args.http_user_agent, logger)
    scraper_run(s, logger)

    # Only print selected item
    sel_item = args.item
    obj_var = get_carrier_items()[sel_item]

    print s.__dict__[obj_var]


def output_term(args):
    """

    :param args: arguments from argparse parser

    Prints a scraper's full list of variables pulled
    """
    # Outputting to terminal selected

    assert(isinstance(args, argparse.Namespace))

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    logger.debug("Using term output")

    if args.password is None:
        password = getpass.getpass(prompt='{} password (will not echo): '.format(args.carrier))
        logger.debug("Password is {} chars long".format(len(password)))
    else:
        password = args.password

    if len(password) < 1:
        logger.warn("Password has no length")

    scraper = scraper_get(args.carrier, args.username, password, args.http_user_agent, logger)
    scraper_run(scraper, logger)
    scraper.print_all()

    return 0


def scraper_get(carrier, username, password, http_user_agent, logger):
    try:
        # Get scraping object - {dict}[item](args) = Object(args)
        scraper = get_carriers()[carrier](username, password, http_user_agent)
        logger.debug("Using object {}".format(type(scraper)))

    except Exception as e:
        logger.error("Failed to run scrapper", exc_info=True)
        sys.exit('An unknown error has occurred: {}'.format(str(e)))

    return scraper


def scraper_run(scraper, logger):
    try:
        scraper.go()
    except Exception as e:
        logger.error("Failed to run scrapper", exc_info=True)
        sys.exit('An unknown error has occurred: {}'.format(str(e)))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\nExiting")
