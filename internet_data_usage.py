#!/usr/bin/env python2

import sys
import logging
import argparse
import re
import getpass
import requests # Handling HTTP Requests and cookies
from bs4 import BeautifulSoup
from ZabbixSender import ZabbixSender, ZabbixPacket
import json
"""
    TODO:
        - Add cookie save/resume (Most time is spent authorizing)
        - Implement Caching (would help with Zabbix)

"""

__version__ = "0.2-HEAD"
__author__ = "Andrew Klaus"
__author_email__ = "andrewklaus@gmail.com"
__copyright__ = "2015"

DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"


def main():
    #logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Top level parsers
    main_parser = argparse.ArgumentParser(
        description="internet_data_usage {version} Copyright (c) {copyright} {author} ({email})\n"
                    .format(version=__version__, copyright=__copyright__, author=__author__, email=__author_email__))
    subparsers = main_parser.add_subparsers(title="subcommands", help="valid subcommands")

    add_term_command(subparsers)
    add_zabbix_command(subparsers)

    args = main_parser.parse_args()

    # Run function for selected subparser
    args.func(args)


def setup_logging(verbosity):
    if verbosity > 0:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.debug("Enable logger debugging")


def get_carrier_items():
    # Mapping for object variables
    carrier_items = {"data_usage" : "_data_usage",
                     "data_plan_total" : "_data_plan_total",
                     "data_use_unit" : "_data_usage_unit",
                     "plan": "_plan",
                     #"days_remaining" : "_days_remaining"
                     }

    return carrier_items


def get_carriers():
    # Dictionary to map carriers to their objects to use
    carriers_dict = {"telus_wireline" : TelusWirelineScraper,
                     "koodo_mobile" : KoodoMobileScraper}

    return carriers_dict


def add_zabbix_command(subparsers):
    # Arguments for zabbix output

    zabbix_parser = subparsers.add_parser("zabbix", help="all output will be sent to a Zabbix server")
    zabbix_parser.add_argument("username", help="Username for account access")
    zabbix_parser.add_argument("password", help="Carrier password for account access")
    zabbix_parser.add_argument("-i", "--item", default='data_usage',
                               help='Item to request (default=data_usage)',
                               choices=get_carrier_items().keys())
    zabbix_parser.add_argument("-c", "--carrier", default='telus_wireline',
                             help='Carrier to query from (default=telus_wireline)',
                             choices=get_carriers().keys())
#    parser.add_argument("-t", "--cache_time", default=0,
#                       type=int, help='Seconds to keep data cached (default=0)')
    zabbix_parser.add_argument("-a", "--http_user_agent", default=DEFAULT_USER_AGENT,
                            help="Defaults to '{}'".format(DEFAULT_USER_AGENT))
    zabbix_parser.add_argument("-v", "--verbose", action="store_true", default=False)

    zabbix_parser.set_defaults(func=output_zabbix)


def add_term_command(subparsers):
    # Arguments for terminal-only output

    term_parser = subparsers.add_parser("term", help="all output will echo in a terminal")
    #term_parser.add_argument("-i", "--item", default='data_usage',
    #                         help='Item to request (default=data_usage)',
    #                         choices=get_carrier_items().keys())
    term_parser.add_argument("username", help="Username for account access")
    term_parser.add_argument("-p", "--password", default=None,
                             help="Carrier password for account access \
                             (will prompt if not specified)")
#    parser.add_argument("-t", "--cache_time", default=0,
#                       type=int, help='Seconds to keep data cached (default=0)')
    term_parser.add_argument("-c", "--carrier", default='telus_wireline',
                             help='Carrier to query from (default=telus_wireline)',
                             choices=get_carriers().keys())

    term_parser.add_argument("-a", "--http_user_agent", default=DEFAULT_USER_AGENT,
                            help="Defaults to '{}'".format(DEFAULT_USER_AGENT))
    term_parser.add_argument("-v", "--verbose", action="store_true", default=False)

    term_parser.set_defaults(func=output_term)


def output_zabbix(args):
    # Outputting to Zabbix selected

    assert(isinstance(args, argparse.Namespace))
    assert(args.password is not None)

    logger = logging.getLogger(__name__)
    setup_logging(args.verbose)
    logger.debug("Using zabbix output")

    scraper = scraper_get(args.carrier, args.username, args.password, args.http_user_agent, logger)
    scraper_run(scraper, logger)

    # Only print selected item
    sel_item = args.item
    obj_var = get_carrier_items()[sel_item]

    print scraper.__dict__[obj_var]

def output_term(args):
    # Outputting to terminal selected

    assert(isinstance(args, argparse.Namespace))

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    logger.debug("Using term output")

    if args.password is None:
        password = getpass.getpass(prompt='CarrieSpecific parser for zabbix password (will not echo): ')
        logger.debug("Password is {} chars long".format(len(password)))
    else:
        password = args.password

    if len(password) < 1:
        logger.warn("Password has no length")

    scraper = scraper_get(args.carrier, args.username, password, args.http_user_agent, logger)
    scraper_run(scraper, logger)
    scraper.print_all()


def scraper_get(carrier, username, password, http_user_agent, logger):
    try:
        # Get scraping object - {dict}[item] = Object(args)
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

class CarrierUsageScraper(object):
    """
    This class should only be inherited by another class.

    name = name of the carrier
    description = description of the carrier
    post_data = HTTP POST data that is passed to the url_login script. Dictionary format.
    http_headers = HTTP Header to use for the website scraping

    url_login = login script that handles the POST authentication and cookies
    url_data = web page that presents the data to parse (post-login)


    """
    def __init__(self, name,
                 description,
                 post_data,
                 url_login,
                 url_data,
                 http_headers,
                 logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self.name = name
        self.description = description
        self.post_data = post_data 
        self.http_headers = http_headers
        
        self.url_login = url_login
        self.url_data = url_data

        self._data_usage = None
        self._plan = None
        self._data_usage_unit = None
        self._data_plan_total = None

    def _login(self):
        # Create web session

        try:
            self.s = requests.session()
            self.s.post(self.url_login, self.post_data, headers=self.http_headers)
        except Exception as e:
            # Login failed
            self.login_failed = 1

        self._logged_in = True

    def get_data_usage(self):
        return self._data_usage

    def get_plan(self):
        return self._plan

    def _get_data_pg_html(self):
        # Returns HTML for data page
        if self._logged_in is not True:
            raise Exception("Not logged in")
        else:
            r = self.s.get(self.url_data, headers=self.http_headers)
            page = BeautifulSoup(r.text.encode("utf8"), "lxml")
        return page
 
    def _parse(self, parse_page):
        pass

    def go(self):
        self._login()

        # Send page html to the parser
        page = self._get_data_pg_html()
        self._parse(page)

    def print_all(self):
        print "{} Plan: {}".format(self.name, self._plan)
        print "Usage: {}/{} {}".format(self._data_usage, self._data_plan_total, self._data_usage_unit)


class TelusWirelineScraper(CarrierUsageScraper):
    """

    Other meaningful data that can be pulled:
    Billing cycle
    Days left in cycle

    """
    def __init__(self, username, password, user_agent):
        name = "TelusWireline"
        description = "Telus Wireline Services (Internet + TTV)"
        url_login = "https://www.telus.com/sso/UI/Login?realm=telus&service=telus&locale=en"
        url_data = "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage"

        post_data = { "goto": "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage",
                    "encoded": "false",
                    "service": "telus",
                    "realm": "telus",
                    "portal": "telus",
                    "userLanguage": "en",
                    "IDToken1": username,
                    "IDToken2": password,
                    "remember-me-checkbox[]" : ""}

        http_headers = {'user-agent': user_agent }

        CarrierUsageScraper.__init__(self, name, description, post_data, url_login, url_data, http_headers)

    def _parse(self, parse_page):
        try:
            plan = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
            self._plan = plan.strip()
            self._data_usage_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
            data_usage = parse_page.find(class_="used").string
            data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()

            # Remove all non-numeric values
            self._data_plan_total = re.sub("[^0-9]", "", data_plan_total)
            self._data_usage = re.sub("[^0-9]", "", data_usage)

        except Exception as e:
            logging.error("Failed to parse Telus Wireline Scraper")
            sys.exit("Unable to parse: {}".format(e.message))

        # Pull json data which gives better in-depth detail
        self._json_url = "https://www.telus.com" + parse_page.find(class_="usage-bar-chart mobile-chart").find(class_="item visually-hidden")["data-url"]


class KoodoMobileScraper(CarrierUsageScraper):
    """

    Other meaningful data that could be pulled:
    Messaging usage
    Airtime usage
    Billing Cycle
    Days left in cycle

    """
    def __init__(self, username, password, user_agent):
        name = "KoodoMobile"
        description = "Koodo Wireless Services"
        url_login = "https://secure.koodomobile.com/sso/UI/Login?realm=koodo"
        url_data = "https://selfserveaccount.koodomobile.com/my-account/usage/overview/usage?INTCMP=KMNew_NavBar_Usage"

        post_data = { "goto": "https://identity.koodomobile.com:443/as/QVVKn/resume/as/authorization.ping",
                    "encoded": "false",
                    "service": "koodo",
                    "realm": "koodo",
                    "portal": "koodo",
                    "locale": "en",
                    "IDToken1": username,
                    "IDToken2": password,
                    "check1": "on",
                    "Login.Submit": "Log in"}

        http_headers = {'user-agent': user_agent }

        CarrierUsageScraper.__init__(self, name, description, post_data, url_login, url_data, http_headers)

    def _parse(self, parse_page):
        try:
            plan = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
            self._plan = plan.strip()
            self._data_usage_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
            data_usage = parse_page.find(class_="used").string
            data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()

            # Remove all non-numeric values
            self._data_plan_total = re.sub("[^0-9]", "", data_plan_total)
            self._data_usage = re.sub("[^0-9]", "", data_usage)

        except Exception as e:
            logging.error("Failed to parse Koodo Mobile Scraper")
            sys.exit("Unable to parse: {}".format(e.message))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\nExiting")
