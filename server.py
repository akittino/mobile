from httplib import OK
from httplib import BAD_REQUEST
from httplib import UNAUTHORIZED
from httplib import FORBIDDEN
from httplib import NOT_ACCEPTABLE
from httplib import PRECONDITION_FAILED


from flask import abort
from flask import jsonify
from flask import request
from flask import Flask

import csv
import os.path
import glob
import random

debug = True

dirDB = "./pDB"

app = Flask(__name__)
data = {}
passwords = {}
tokens = {}


def create_token(user):
    token = ""
    while len(token) != 3:
        token += str(random.randint(0, 9))
    token += 'z'
    if user not in tokens:
        tokens[user] = []
    tokens[user].append(token)
    return token


def save_passwords():
    pf = csv.writer(open(dirDB + "/hashes.csv", "w"))
    for key, val in passwords.items():
        pf.writerow([key, val])


def load_passwords():
    if os.path.isfile(dirDB + "/hashes.csv"):
        for key, val in csv.reader(open(dirDB + "/hashes.csv")):
            passwords[key] = val


def save_data():
    if not os.path.exists(dirDB):
        os.makedirs(dirDB)

    for u in data:
        if u == "":
            pass
        else:
            path = os.path.join(dirDB, u + "_data.csv")
            f = csv.writer(open(path, "w"))
            for key, val in data[u].items():
                f.writerow([key, val])

    save_passwords()


def load_data():
    if os.path.exists(dirDB):
        files_path = os.path.join(dirDB, "*_data.csv")
        files = glob.glob(files_path)
        for f in files:
            _, filename = os.path.split(f)
            name = filename[:-9]
            data[name] = {}
            for key, val in csv.reader(open(f)):
                data[name][key] = val
        load_passwords()
    print data


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


#  LOG IN
@app.route('/user', methods=['POST'])
def login_user():
    if (not request.json) or ('userName' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['userName'])
    if name not in data:
        abort(PRECONDITION_FAILED)
    if passwords[name] != str(request.json['pwd']):
        abort(FORBIDDEN)
    else:
        t = create_token(name)
        return jsonify(token=t), OK


#  LOG OUT
@app.route('/user', methods=['DELETE'])
def logout_user():
    if (not request.json) or ('userName' not in request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['userName'])
    token = str(request.json['token'])

    if token not in tokens[name]:
        abort(UNAUTHORIZED)

    if name not in data:
        abort(PRECONDITION_FAILED)
    else:
        tokens[name].remove(token)
        return jsonify(), OK


#  ADD USER
@app.route('/user', methods=['PUT'])
def add_user():
    if (not request.json) or ('userName' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['userName'])
    if name in data:
        abort(PRECONDITION_FAILED)
    else:
        data[name] = {}
        passwords[name] = str(request.json['pwd'])
        t = create_token(name)
        return jsonify(token=t), OK


#  SHOW ALL
@app.route('/product/all', methods=['POST'])
def show_all_products():

    if (not request.json) or ('userName' not in request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)
    user = str(request.json['userName'])
    token = str(request.json['token'])
    if token not in tokens[user]:
        abort(UNAUTHORIZED)
    return jsonify(**(data[user]))


#  DELETE
@app.route('/product', methods=['DELETE'])
def delete_product():
    if (not request.json) or ('name' not in request.json)\
            or ('userName' not in request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)

    product = str(request.json['name'])

    user = str(request.json['userName'])
    token = str(request.json['token'])
    if token not in tokens[user]:
        abort(UNAUTHORIZED)

    if product in data[user].keys():
        data[user].pop(product)
        save_data()
        return jsonify(), OK
    else:
        abort(PRECONDITION_FAILED)


#  ADD
@app.route('/product', methods=['POST'])
def add_product():
    if (not request.json) or ('name' not in request.json)\
            or ('userName' not in request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)

    product = str(request.json['name'])

    user = str(request.json['userName'])
    token = str(request.json['token'])
    if token not in tokens[user]:
        abort(UNAUTHORIZED)

    if product in data[user].keys():
        abort(PRECONDITION_FAILED)

    else:
        data[user][product] = 0
        save_data()
        return jsonify(), OK


#  CHANGE
@app.route('/product', methods=['PUT'])
def change_product():
    if (not request.json) or ('name' not in request.json) \
            or ('change' not in request.json) or (not is_int(request.json['change']))\
            or ('userName' not in request.json) or ('token' not in request.json):
        abort(BAD_REQUEST)

    product = str(request.json['name'])
    change = int(request.json['change'])

    user = str(request.json['userName'])
    token = str(request.json['token'])
    if token not in tokens[user]:
        abort(UNAUTHORIZED)

    if product in data[user].keys():
        quantity = int(data[user][product])
        quantity += change

        if quantity < 0:
            abort(NOT_ACCEPTABLE)

        data[user][product] = str(quantity)
        save_data()
        return jsonify(name=product, value=data[user][product]), OK

    else:
        abort(PRECONDITION_FAILED)

if __name__ == '__main__':
    load_data()
    app.run(host='127.0.0.1', port=5678, debug=debug)
