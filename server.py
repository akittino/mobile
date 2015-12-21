from httplib import OK
from httplib import BAD_REQUEST
from httplib import UNAUTHORIZED
from httplib import FORBIDDEN
from httplib import PRECONDITION_FAILED


from flask import abort
from flask import jsonify
from flask import request
from flask import Flask

import random
import json

debug = True

token_parts = '1234567890qwertyuiopasdfghjklzxcvbnm'

app = Flask(__name__)

passwords = {}
tokens = {}
totalList = {}
productList = {}


def create_token(user):
    global tokens
    token = ""
    while len(token) != 30:
        token += str(random.choice(token_parts))
    tokens[token] = user
    if user not in totalList:
        totalList[user] = []
    if user not in productList:
        productList[user] = {}
    productList[user][token] = {}
    print tokens
    return token


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


#  SYNC
@app.route('/sync', methods=['POST'])
def sync():
    if (not request.json) or ('token' not in request.json) or ('product' not in request.json):
        abort(BAD_REQUEST)

    token = str(request.json['token'])
    print "token-> ",
    print token
    print tokens
    if token not in tokens:
        abort(UNAUTHORIZED)

    user = tokens[token]
    newdata = {}
    if request.json['product'] != "empty":
        tmp = request.json['product']
        if type(tmp) is dict:
            newdata = tmp
        else:
            newdata = json.loads(tmp)

    olddata = productList[user][token]
    total = totalList[user]

    print ""
    print "newdata->"
    print newdata

    print ""
    print "olddata->"
    print olddata

    exitdata = {}

    allkeys = []
    for key in newdata:
        allkeys.append(key)
    for key in olddata:
        allkeys.append(key)
    for key in total:
        allkeys.append(key)
    allkeys = set(allkeys)

#  e -> exists     ne -> not exists
#  id totalList | olddata | newdata || endTotal | exitdata
# . 1   e       |   e     |   e     ||   e      |   e    +
# . 2   e       |   e     |   ne    ||   ne  -  |   ne
# . 3   e       |   ne    |   e     ||   e      |   e    +
# . 4   e       |   ne    |   ne    ||   e      |   e    +
# . 5   ne      |   e     |   e     ||   ne     |   ne
# . 6   ne      |   e     |   ne    ||   ne     |   ne
# . 7   ne      |   ne    |   e     ||   e   +  |   e    +
# . 8   ne      |   ne    |   ne    ||   ne     |   ne

    for key in allkeys:
        if key in total and key in olddata and key in newdata:
            # 1
            exitdata[key] = newdata[key]

        elif key in total and key in olddata and key not in newdata:
            # 2
            total.remove(key)

        elif key in total and key not in olddata and key in newdata:
            # 3
            exitdata[key] = newdata[key]

        elif key in total and key not in olddata and key not in newdata:
            # 4
            exitdata[key] = 0
        elif key not in total and key in olddata and key in newdata:
            # 5
            pass

        elif key not in total and key in olddata and key not in newdata:
            # 6
            pass

        elif key not in total and key not in olddata and key in newdata:
            # 7
            exitdata[key] = newdata[key]
            total.append(key)

        elif key not in total and key not in olddata and key not in newdata:
            # 8
            pass

    productList[user][token] = exitdata
    totalList[user] = total

    othersdata = {}

    for key in total:
        othersdata[key] = 0

    for t, products in productList[user].iteritems():
        if t != token:
            for key, value in products.iteritems():
                if key in othersdata:
                    othersdata[key] += value

    print ""
    print "productList ->",
    print productList[user]
    print ""
    print "othersdata ->",
    print othersdata
    print ""

    print ""
    print "total->"
    print total

    return jsonify(**othersdata), OK


#  LOG IN
@app.route('/user', methods=['POST'])
def login_user():
    if (not request.json) or ('userName' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['userName'])
    if name not in passwords:
        abort(PRECONDITION_FAILED)
    if passwords[name] != str(request.json['pwd']):
        abort(FORBIDDEN)
    else:
        t = create_token(name)
        return jsonify(token=t), OK


#  LOG OUT
@app.route('/user', methods=['DELETE'])
def logout_user():
    if (not request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)
    token = str(request.json['token'])

    if token not in tokens:
        abort(UNAUTHORIZED)
    else:
        del tokens[token]
        return jsonify(), OK


#  REGISTER
@app.route('/user', methods=['PUT'])
def add_user():
    if (not request.json) or ('userName' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['userName'])
    if name in passwords:
        abort(PRECONDITION_FAILED)
    else:
        passwords[name] = str(request.json['pwd'])
        t = create_token(name)
        return jsonify(token=t), OK


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5678, debug=debug)
