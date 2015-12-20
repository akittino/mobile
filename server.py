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
    if token not in tokens:
        abort(UNAUTHORIZED)

    user = tokens[token]
    newdata = request.json['product']
    olddata = productList[user][token]
    total = totalList[user]

    exitdata = {}

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

    for key, value in newdata.iteritems():
        if key in olddata and key in total:  # 1
            exitdata[key] = value
        elif key not in olddata and key in total:  # 3
            exitdata[key] = value
        elif key in olddata and key not in total:  # 5
            pass
        elif key not in olddata and key not in total:  # 7
            exitdata[key] = value
            total.append(key)

    for key, value in olddata.iteritems():
        if key not in newdata and key in total:  # 2
            total.remove(key)
        elif key not in newdata and key not in total:  # 6
            pass

    for key in total:
        if key not in olddata and key not in newdata:  # 4
            exitdata[key] = 0

    productList[user][token] = exitdata

    othersdata = {}

    for key in total:
        othersdata[key] = 0

    for t, products in productList[user].iteritems():
        if t != token:
            for key, value in products.iteritems():
                if key in othersdata:
                    othersdata[key] += value

    print productList[user]

    return jsonify(othersdata=othersdata), OK


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
