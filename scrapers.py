import logging
import re
import requests
from bs4 import BeautifulSoup
import sys


class CarrierUsageScraper(object):
    """
    This class should only be inherited by another class.

    name = name of the carrier
    description = description of the carrier
    post_data = HTTP POST data that is passed to the url_login script. Dictionary format.
    http_headers = HTTP Header to use for the website scraping

    url_login = login script that handles the POST authentication and cookies
    url_data = web page that presents the data to parse (post-login)

    A _parse method is required to be created at the minimum

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
        print "Days left: {}".format(self._days_left)


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
            days_left = parse_page.find(class_="meters-bill-cycle").p.strong.string

            # Remove all non-numeric values
            self._data_plan_total = re.sub("[^0-9]", "", data_plan_total)
            self._data_usage = re.sub("[^0-9]", "", data_usage)
            self._days_left = re.sub("[^0-9]", "", days_left)

        # <div class="meters-bill-cycle" tabindex="0">
        #   <p>
        #     <span class="frg-icon icon-calendar" aria-hidden="true"></span>
        #     Current cycle
        #     October 13, 2015 - November 12, 2015
        #     &mdash;
        #     <strong>19 days left</strong>
        #   </p>
        # </div>

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
            days_left = parse_page.find(class_="records-header-info").strong.string

            # Remove all non-numeric values
            self._data_plan_total = re.sub("[^0-9]", "", data_plan_total)
            self._data_usage = re.sub("[^0-9]", "", data_usage)
            self._days_left = re.sub("[^0-9]", "", days_left)

        except Exception as e:
            logging.error("Failed to parse Koodo Mobile Scraper")
            sys.exit("Unable to parse: {}".format(e.message))