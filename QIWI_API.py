import urllib.request
import urllib.parse
import json
import time
import requests


class QiwiError(Exception):
    pass


class SyntaxisError(QiwiError):
    def __init__(self):
        self.text = "Query execution failed"


class TokenError(QiwiError):
    def __init__(self):
        self.text = "Wrong TOKEN"


class NoRightsError(QiwiError):
     def __init__(self):
        self.text = "No right"


class TransactionNotFound(QiwiError):
    def __init__(self):
        self.text = "Transaction not found or missing payments with specified characteristics"


class WalletError(QiwiError):
    def __init__(self):
        self.text = "Wallet not found"


class HistoryError(QiwiError):
    def __init__(self):
        self.text = "Too many requests, the service is temporarily unavailable"


class MapError(QiwiError):
    def __init__(self):
        self.text = "Map processing errors"


class NotFoundAddress(MapError):
    def __init__(self):
        self.text = "Could not find address"


class CheckError(QiwiError):
    def __init__(self):
        self.text = "Could not get check"


class WrongEmail(CheckError):
    def __init__(self):
        self.text = "Wrong Email address"


class WrongNumber(QiwiError):
    def __init__(self):
        self.text = "Wrong phone number"


class TransactionError(QiwiError):
    def __init__(self):
        self.text = "Failed to carry out the transaction"


def run_the_query(headers, url):
    try:
        req = urllib.request.Request(url, headers=headers)
        html = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        return html
    except:
        return False


def found_address(ip):
    try:
        response = requests.get('http://freegeoip.net/json/{}'.format(ip))
        if response:
            json_response = response.json()
            return json_response["city"]
        else:
            return False
    except:
        return False


def write_file(headers, url, file_name):
    try:
        req = urllib.request.Request(url, headers=headers)

        with open(file_name, mode='wb') as f:
            res = urllib.request.urlopen(req).read()
            f.write(res)

        return True
    except:
        return False


def found_id(number):
    headers = {"Accept": "application/json",
               "Content-Type": "application/x-www-form-urlencoded"}
    data = urllib.parse.urlencode({"phone": "+" + number})
    try:
        request = requests.post("https://qiwi.com/mobile/detect.action", data=data, headers=headers)
        if request:
            answer = request.json()
            if answer["code"]["value"] != '0':
                return False
            return answer["message"]

        else:
            return False
    except:
        return False


class UserQiwi:
    url = "https://edge.qiwi.com/"

    def __init__(self, token):
        self.token = token
        self.headers = {"Accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": "Bearer {}".format(self.token)}
        self.urls = {"Profile": (UserQiwi.url + "person-profile/v1/profile/current?", ["authInfoEnabled",
                                                                                       "contractInfoEnabled",
                                                                                       "userInfoEnabled"]),
                     "Balance": (UserQiwi.url + "funding-sources/v1/accounts/current", None),
                     "Transactions": (UserQiwi.url + "payment-history/v2/persons/{}/payments?rows={}", None),
                     "Transaction": (UserQiwi.url + "payment-history/v2/transactions/{}", None),
                     "Check": (UserQiwi.url + "payment-history/v1/transactions/{}/cheque/{}?type={}{}",
                               None),
                     "Phone pay": (UserQiwi.url + "sinap/api/v2/terms/{}/payments", None),
                     "Qiwi pay": (UserQiwi.url + "sinap/api/v2/terms/99/payments", None)}
        self.currency = {643: "RUB",
                         840: "USD",
                         978: "EUR",
                         "Not Stated": "Not Stated"}
        self.identification = {"ANONYMOUS": "без идентификации",
                               "SIMPLE": "упрощенная идентификация (SIMPLE)",
                               "VERIFIED": "упрощенная идентификация (VERIFIED)",
                               "FULL": "полная идентификация",
                               "Not Stated": "Not Stated"}
        self.user_date = None

        try:
            self.update_info()
        except:
            raise TokenError

    def change_token(self, new_token):
        self.token = new_token

        if not run_the_query(self.headers, self.urls["Profile"][0]):
            raise TokenError

    def get_user_token(self):
        return self.token

    def get_balance(self):
        try:
            answer = run_the_query(self.headers, self.urls["Balance"][0])["accounts"]

            report = ["Balance {}\n-----------------------".format(time.asctime())]
            for i in answer:
                if i["balance"]:
                    report.append("{}: {} {}".format(i["alias"],
                                                     i["balance"]["amount"],
                                                     self.currency[i["balance"]["currency"]]))
                else:
                    report.append("{}: {}".format(i["alias"], "Not Stated"))

            return "\n".join(report)
        except:
            raise QiwiError

    def update_info(self):
        try:
            answer = run_the_query(self.headers, self.urls["Profile"][0])
            comands_info = {'email': answer["authInfo"]['boundEmail'],
                            'last_ip': answer["authInfo"]['ip'],
                            'last_login': answer["authInfo"]['lastLoginDate'],
                            'last_mob_pin_ch': answer["authInfo"]['mobilePinInfo']['lastMobilePinChange'],
                            'next_mob_pin_ch': answer["authInfo"]['mobilePinInfo']['nextMobilePinChange'],
                            'last_pass_ch': answer["authInfo"]['passInfo']['lastPassChange'],
                            'next_pass_ch': answer["authInfo"]['passInfo']['nextPassChange'],
                            'id': answer["authInfo"]['personId'],
                            'reg_date': answer["authInfo"]['registrationDate'],
                            'status': answer["contractInfo"]["blocked"],
                            'ident_info': tuple(map(lambda x: (x["bankAlias"],
                                                               self.identification[x["identificationLevel"]]),
                                                    answer["contractInfo"]["identificationInfo"])),
                            'default_alias': answer['userInfo']['defaultPayAccountAlias'],
                            'default_cur': answer['userInfo']['defaultPayCurrency'],
                            'first_tr_id': answer['userInfo']['firstTxnId'],
                            'operator': answer['userInfo']['operator']}
            self.user_date = {}
            for i in comands_info:
                if comands_info[i] is None or comands_info[i] == 'null' or not comands_info[i]:
                    self.user_date[i] = 'Not Stated'
                else:
                    self.user_date[i] = comands_info[i]
        except:
            raise QiwiError

    def get_info(self):
        return "User: {} {}\nEmail: {}\nRegistration date: {}\nStatus: {}\nLast ip: {}\nLast change password: {}\n" \
               "Last change mobile pin: {}\nNext change password: {}\nNext change mobile pin: {}\n" \
               "Ident info: \n--{}\nDefault alias: {}\nDefault currency: {}\n" \
               "First transaction: {}".format(self.user_date['id'], self.user_date['operator'], self.user_date['email'],
                                              self.user_date['reg_date'], self.user_date['status'],
                                              self.user_date['last_ip'], self.user_date['last_pass_ch'],
                                              self.user_date['last_mob_pin_ch'], self.user_date['next_pass_ch'],
                                              self.user_date['next_mob_pin_ch'],
                                              "\n--".join(map(lambda x: ": ".join(x), self.user_date['ident_info'])),
                                              self.user_date['default_alias'],
                                              self.currency[self.user_date['default_cur']],
                                              self.user_date['first_tr_id'])

    def get_last_transactions(self, rows=10):
        transactions = []

        try:
            answer = run_the_query(self.headers, self.urls["Transactions"][0].format(self.user_date["id"], rows))[
                "data"]
            for i in answer:
                transactions.append(["Name: {}".format(i["view"]["title"] + "\n      " + i["view"]["account"]),
                                     "Data: {}".format(i["date"]),
                                     "Status: {}".format(i["status"]),
                                     "Error: {}".format(i["error"]),
                                     "Number transaction: {}".format(i["txnId"]),
                                     "Commission: {} {}".format(i["commission"]["amount"],
                                                                self.currency[i["commission"]["currency"]]),
                                     "Total: {} {}".format(i["total"]["amount"],
                                                           self.currency[i["total"]["currency"]])])
        except:
            raise TransactionNotFound

        return "\n------------------------\n".join(["\n".join(i) for i in transactions])

    def get_info_about_transaction(self, transaction_id):
        try:
            answer = run_the_query(self.headers, self.urls["Transaction"][0].format(transaction_id))
            return "\n".join(["Name: {}".format(answer["view"]["title"] + "\n      " + answer["view"]["account"]),
                              "Data: {}".format(answer["date"]),
                              "Status: {}".format(answer["status"]),
                              "Error: {}".format(answer["error"]),
                              "Number transaction: {}".format(answer["txnId"]),
                              "Commission: {} {}".format(answer["commission"]["amount"],
                                                         self.currency[answer["commission"]["currency"]]),
                              "Total: {} {}".format(answer["total"]["amount"],
                                                    self.currency[answer["total"]["currency"]])])
        except:
            raise TransactionNotFound

    def get_map_terminates(self, address=None):
        if not address:
            address = found_address(self.user_date["last_ip"])

        geocoder_url = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {"geocode": address,
                           "format": "json"}
        try:
            response = requests.get(geocoder_url, params=geocoder_params)
            if response:
                json_response = response.json()
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                components = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"]
                try:
                    locality = [i["name"] for i in components if i["kind"] == "locality"][0]
                except IndexError:
                    locality = address

            geocoder_params["geocode"] = locality
            response = requests.get(geocoder_url, params=geocoder_params)
            if response:
                json_response = response.json()
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                coords = (tuple(map(float, toponym['boundedBy']['Envelope']['lowerCorner'].split())),
                          tuple(map(float, toponym['boundedBy']['Envelope']['upperCorner'].split())))
            else:
                raise NotFoundAddress
        except:
            raise MapError

        headers = {'Accept': 'application/json;charset=UTF-8'}
        coordinates = ["latNW={}".format(coords[1][1]),
                       "lngNW={}".format(coords[0][0]),
                       "latSE={}".format(coords[0][1]),
                       "lngSE={}".format(coords[1][0])]
        try:
            req = urllib.request.Request(
                'https://edge.qiwi.com/locator/v2/nearest/clusters?{}&zoom=10'.format("&".join(coordinates)),
                headers=headers)
            answer = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
            address = [i["address"] for i in answer]
            coordinate = [(i["coordinate"]["longitude"], i["coordinate"]["latitude"]) for i in answer]
        except:
            raise MapError

        map_params = {
            "l": "map",
            "pt": "~".join([",".join(map(str, i)) + ",pm2dom" for i in coordinate]),
            "bbox": "~".join([",".join((str(coords[0][0]), str(coords[1][1]))),
                              ",".join((str(coords[1][0]), str(coords[0][1])))])
        }

        map_api_server = "http://static-maps.yandex.ru/1.x/"

        try:
            response = requests.get(map_api_server, params=map_params)

            if not response:
                raise MapError
        except:
            raise MapError

        return map_api_server + "?l={}&pt={}&bbox={}".format(map_params["l"], map_params["pt"],
                                                             map_params["bbox"]), address

    def get_image_check(self, transaction_id, file_name="check.jpg"):
        answer = run_the_query(self.headers, self.urls["Transaction"][0].format(transaction_id))

        if not answer:
            raise TransactionNotFound

        typ = answer['type']
        write = write_file(self.headers, self.urls["Check"][0].format(transaction_id, "file", typ, "&format=JPEG"),
                           file_name)

        if not write:
            raise CheckError

        return True

    def send_check_email(self, transaction_id, email=None):
        answer = run_the_query(self.headers, self.urls["Transaction"][0].format(transaction_id))

        if not answer:
            raise TransactionNotFound

        typ = answer['type']
        email = {"email": self.user_date["email"] if email is None else email}

        request = requests.post(self.urls["Check"][0].format(transaction_id, "send", typ, ''),
                                data=json.dumps(email),
                                headers=self.headers)
        if request:
            return True
        else:
            raise WrongEmail

    def transaction_telephone(self, amount, number=None):
        if number is None:
            number = str(self.user_date["id"])

        number_id = found_id(number)

        if not number_id:
            raise WrongNumber

        number = number[1:]

        try:
            amount = round(float(amount), 2)
        except TypeError:
            raise WalletError

        data = {"id": str(int(time.time() * 1000)),
                "sum": {"amount": amount,
                        "currency": "643"},
                "paymentMethod": {"type": "Account",
                                  "accountId": "643"},
                "fields": {"account": number}}

        try:
            request = requests.post(self.urls["Phone pay"][0].format(number_id), data=json.dumps(data),
                                    headers=self.headers)
            if request:
                answer = request.json()
                return "Successfully. Transaction ID: {}".format(answer["transaction"]["id"])
            else:
                raise TransactionError
        except:
            raise TransactionError

    def transaction_qiwi(self, account_id, amount):
        try:
            amount = round(float(amount), 2)
        except ValueError:
            raise WalletError

        data = {"id": str(int(time.time() * 1000)),
                "sum": {"amount": amount,
                        "currency": "643"},
                "paymentMethod": {"type": "Account",
                                  "accountId": "643"},
                "comment": "test",
                "fields": {"account": account_id}}

        try:
            request = requests.post(self.urls["Qiwi pay"][0], data=json.dumps(data), headers=self.headers)
            if request:
                answer = request.json()
                return "Successfully. Transaction ID: {}".format(answer["transaction"]["id"])
            else:
                raise TransactionError
        except:
            raise TransactionError
