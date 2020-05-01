from dotenv import load_dotenv
from os import getenv
from sys import argv
import requests
import json
from datetime import datetime, timedelta
import pytz


DEBUG_ENABLED = '-d' in argv


def debug(msg):
    """If in debug mode, send a debug message to stdout."""
    if DEBUG_ENABLED:
        print("Debug: {}".format(msg))


class Shopify:

    def __init__(self):
        """Get ready tp make calls to Shopify API."""

        load_dotenv(verbose=True)       # Set operating system environment variables based on contents of .env file.

        shop_name = getenv('SHOP_NAME')
        api_version = getenv('API_VERSION')
        api_key = getenv('API_KEY')
        password = getenv('PASSWORD')

        self.shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s/" % (api_key,
                                                                          password,
                                                                          shop_name,
                                                                          api_version)

        self.orders = []                # List of orders returned by most recent use of get_orders() method.
        self.money_format = ''          # Eg. '£{{amount}}'
        self.timezone = ''              # Eg. '(GMT+00:00) Europe/London'
        self.timezone_offset = ''       # Eg. '+01:00'

    def get_store_info(self):
        """Obtain some reference data about the store."""

        # API documentation, https://shopify.dev/docs/admin-api/rest/reference/store-properties/shop

        url = self.shop_url + 'shop.json'       # Shop API
        request = requests.get(url)

        if request.status_code != 200:
            debug('Shopify.get_store_info : request.status_code = '.format(request.status_code))
        else:
            request_dict = json.loads(s=request.text)
            request_shop = request_dict['shop']

            self.money_format = request_shop['money_format']
            self.timezone = request_shop['timezone']
            self.timezone_offset = self.timezone[4:10]

            debug('Shopify.get_store_info : self.money_format = {}'.format(self.money_format))
            debug('Shopify.get_store_info : self.timezone = {}'.format(self.timezone))
            debug('Shopify.get_store_info : self.timezone_offset = {}'.format(self.timezone_offset))

    @staticmethod
    def is_date(test: str) -> bool:
        """Return true iff the parm string is a valid date in format yyyy-mm-dd. For example '2020-04-29'."""
        if len(test) != 10:
            debug('Shopify.is_date : test = {}'.format(test))
            return False
        year = test[0:4]
        month = test[5:7]
        day = test[8:10]

        if year.isdecimal() and month.isdecimal() and day.isdecimal():
            return True
        debug('Shopify.is_date : year = {}  month = {}  day = {}'.format(year, month, day))
        return False

    @staticmethod
    def date_from_datetime(date_time: str) -> str:
        """For parm datetime string in format yyyy-mm-ddThh:mm:ss+zz:zz, return the date part only."""
        date_only = date_time[0:10]
        return date_only

    def get_orders(self, from_date: str, to_date: str):
        """Create a list of orders between parm From and To dates."""

        # Both parms should be valid date strings.
        assert self.is_date(test=from_date)
        assert self.is_date(test=to_date)

        # API documented here, https://shopify.dev/docs/admin-api/rest/reference/orders/order#index-2020-04
        url = (self.shop_url
               + 'orders.json'                                  # Orders API.
               + '?created_at_min=' + from_date + 'T00:00:00' + self.timezone_offset
               + '&created_at_max=' + to_date + 'T23:59:59' + self.timezone_offset
               + '&status=any'                                  # By default, API only returns open orders.
               + '&limit=250'                                    # This is the maximum.
               + '&fields=id,created_at,total_price,status,financial_status')

        # TODO Proper pagination, in case there are more than 250 orders in the time range.

        request = requests.get(url)
        if request.status_code != 200:
            debug('Shopify.get_orders : request.status_code = '.format(request.status_code))
            self.orders = None
        else:
            request_dict = json.loads(s=request.text)
            if DEBUG_ENABLED:
                print('Shopify.get_orders : request_dict =', request_dict)

            request_orders = request_dict['orders']
            if DEBUG_ENABLED:
                print('Shopify.get_orders : orders =', request_orders)
            self.orders = request_orders

    def orders_on_date(self, target_date: str) -> list:
        """For parm date (in yyyy-mm-dd format), return a list containing the orders on that day."""
        assert self.is_date(target_date)

        output = []
        for each_order in self.orders:
            order_date = self.date_from_datetime(each_order['created_at'])
            if order_date == target_date:
                output.append(each_order)
        return output

    @staticmethod
    def count_orders(orders):
        """Return count of orders."""
        return len(orders)

    def gross_sales(self, target_date: str) -> float:
        """Return the gross amount of sales in the shop currency on parm day.
           Sales are returned as both an integer and a formatted strong."""
        total = 0.00
        orders = self.orders_on_date(target_date)

        for each_order in orders:
            total += float(each_order['total_price'])

        return total


class Skill:

    @staticmethod
    def date_as_str(delta_days: int) -> str:
        """Return a date relative to today as a string in yyyy-mm-dd format."""

        now = datetime.now(pytz.utc)
        local_now = now.astimezone(pytz.timezone('Europe/London'))
        print('now = {}   local_now = {}'.format(now, local_now))

        required_date = local_now + timedelta(days=delta_days)
        return required_date.strftime('%Y-%m-%d')

    def formatted_money(self, money: float) -> (int, str):
        """Return parm real as a tuple (integer amount of the money, string of money).
           The string includes the currency symbol."""

        # See, https://kite.com/python/answers/how-to-format-currency-in-python
        total_as_str = "{:,.2f}".format(round(money, 2))                   # Round to nearest penny / cent.

        sales_str = self.shop.money_format.replace('{{amount}}', total_as_str)
        return int(money), sales_str

    def __init__(self):
        self.shop = Shopify()
        self.shop.get_store_info()                      # Populate attributes with basic shop info.

    def number_orders_today(self) -> str:
        """Return a string saying how many orders there have been today so far."""

        # TODO New functions for today_str and yesterday_str

        today = self.date_as_str(delta_days=0)          # Zero days from today=today.
        orders = self.shop.orders_on_date(today)
        num_orders = self.shop.count_orders(orders)

        if num_orders == 0:
            return 'You have had no orders yet today.'
        elif num_orders == 1:
            return 'You have had 1 order so far today.'
        else:
            return 'You have had {} orders so far today.'.format(num_orders)

    def number_orders_yesterday(self) -> str:
        """Return a string saying how many orders there were yesterday."""
        yesterday = self.date_as_str(delta_days=-1)          # Zero days from today=today.
        orders = self.shop.orders_on_date(yesterday)
        num_orders = self.shop.count_orders(orders)

        if num_orders == 0:
            return 'You had no orders yesterday.'
        elif num_orders == 1:
            return 'You had 1 order yesterday.'
        else:
            return 'You had {} orders yesterday.'.format(num_orders)

    def gross_sales_today(self) -> str:
        """Return a string saying what the gross sales are today so far."""
        today = self.date_as_str(delta_days=0)                  # Zero days from today=today.
        sales = self.shop.gross_sales(today)                    # Obtain today's sales as a float.
        sales_int, sales_str = self.formatted_money(sales)      # Obtain formatted string of the sales.

        if sales_int == 0:
            return 'No sales yet today.'
        else:
            return 'Gross sales so far today are {}'.format(sales_str)

    def gross_sales_yesterday(self) -> str:
        """Return a string saying what the gross sales were yesterday."""
        yesterday = self.date_as_str(delta_days=-1)          # -1 days from today=yesterday.
        sales = self.shop.gross_sales(yesterday)                    # Obtain today's sales as a float.
        sales_int, sales_str = self.formatted_money(sales)      # Obtain formatted string of the sales.

        if sales_int == 0:
            return 'No sales yesterday.'
        else:
            return 'Gross sales yesterday were {}'.format(sales_str)

    def most_recent_order(self) -> str:
        """Return a sting with details of the most recent order."""
        if len(self.shop.orders) == 0:
            return 'There are no recent orders.'
        else:
            order = self.shop.orders[0]          # First order in the list is the most recent one.

            money = float(order['total_price'])
            _, money_str = self.formatted_money(money)

            datetime_format1 = '%Y-%m-%d %H:%M:%S'
            datetime_format2 = '%Y-%m-%dT%H:%M:%S'

            now_utc = datetime.now(pytz.utc)
            # Obtained from, https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
            local_now = now_utc.astimezone(pytz.timezone('Europe/London'))
            local_now_str = str(local_now)
            now_dt = datetime.strptime(local_now_str[0:19], datetime_format1)
            print('now_utc = {}   local_now = {}   local_now_str = {}   now_dt = {}'
                  .format(now_utc, local_now, local_now_str, now_dt))

            order_time_str = order['created_at']
            order_dt = datetime.strptime(order_time_str[0:19], datetime_format2)
            print('order_time_str = {}   order_dt = {}'.format(order_time_str, order_dt))

            diff = now_dt - order_dt
            diff_mins = int(diff.seconds / 60)
            hours = diff_mins // 60
            mins = diff_mins % 60
            print('diff = {}   dif_mins = {}   hours = {}  mins = {}'.format(diff, diff_mins, hours, mins))

            if diff_mins <= 2:
                return 'The most recent order was just now for ' + money_str
            elif hours == 0:
                return 'The most recent order was ' + str(diff_mins) + ' minutes ago for ' + money_str
            elif hours == 1:
                if mins == 0:
                    return 'The most recent order was exactly 1 hour ago for ' + money_str
                if mins == 1:
                    return 'The most recent order was 1 hour and 1 minute ago for ' + money_str
                else:
                    return 'The most recent order was 1 hour and ' + str(mins) + ' minutes ago for ' + money_str
            elif mins == 0:
                return 'The most recent order was exactly ' + str(hours) + ' hours ago for ' + money_str
            elif mins == 1:
                return 'The most recent order was ' + str(hours) + ' hours and 1 minute ago for ' + money_str
            else:
                return 'The most recent order was ' + str(hours) + ' hours and ' + str(mins) + ' minutes ago for '\
                       + money_str


def build_speech_response(title: str, ssml_output: str, plain_output: str) -> dict:
    """Build a speech JSON representation of the title, output text, and end of session."""

    # In this app, the session always ends after a single response.
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': ssml_output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': plain_output
        },
        'shouldEndSession': True
    }


def build_response(session_attributes, speech_response):
    """Build the full response JSON from the speech response."""
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speech_response
    }


def lambda_handler(event, context):
    """Function called by Lambda. Output JSON returned to Alexa."""
    assert(event is not '')
    assert(context is not '')

    print('event =', event)
    print('context =', context)

    this_skill = Skill()
    this_skill.shop.get_store_info()

    today = this_skill.date_as_str(delta_days=0)
    two_days_ago = this_skill.date_as_str(delta_days=-2)
    this_skill.shop.get_orders(from_date=two_days_ago, to_date=today)

    # Default message.
    message = 'Hi, this is the Shopify Alexa skill. You can ask me things like, "How many orders have I had today?"'

    if event['request']['type'] == "IntentRequest":
        intent = event['request']['intent']['name']
        print('intent =', intent)

        if intent == 'OrdersTodayIntent':
            message = this_skill.number_orders_today()
        elif intent == 'OrdersYesterdayIntent':
            message = this_skill.number_orders_yesterday()
        elif intent == 'GrossSalesTodayIntent':
            message = this_skill.gross_sales_today()
        elif intent == 'GrossSalesYesterdayIntent':
            message = this_skill.gross_sales_yesterday()
        elif intent == 'MostRecentOrderIntent':
            message = this_skill.most_recent_order()

    card_title = 'Shopify Skill'
    speech_output = '<speak>' + message + '</speak>'
    card_output = message
    return build_response(session_attributes={},
                          speech_response=build_speech_response(title=card_title,
                                                                ssml_output=speech_output,
                                                                plain_output=card_output))
