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

debug = True

dirDB = "./pDB"

app = Flask(__name__)
userName = ""
data = {}
passwords = {}


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
    if not os.path.exists(dirDB):
        pass
    else:
        files_path = os.path.join(dirDB, "*_data.csv")
        files = glob.glob(files_path)
        for f in files:
            _, filename = os.path.split(f)
            name = filename[:-9]
            data[name] = {}
            for key, val in csv.reader(open(f)):
                data[name][key] = val
        load_passwords()


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


#  LOG IN
@app.route('/user', methods=['POST'])
def login_user():
    global userName
    if (not request.json) or ('name' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['name'])
    if name not in data:
        abort(PRECONDITION_FAILED)
    if passwords[name] != str(request.json['pwd']):
        abort(FORBIDDEN)
    else:
        userName = name
        return jsonify(), OK


#  LOG OUT
@app.route('/user', methods=['DELETE'])
def logout_user():
    global userName
    if userName == "":
        abort(UNAUTHORIZED)
    if (not request.json) or ('name' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['name'])
    if name not in data:
        abort(PRECONDITION_FAILED)
    else:
        userName = ""
        return jsonify(), OK


#  ADD USER
@app.route('/user', methods=['PUT'])
def add_user():
    global userName
    if (not request.json) or ('name' not in request.json) or ('pwd' not in request.json):
        abort(BAD_REQUEST)
    name = str(request.json['name'])
    if name in data:
        abort(PRECONDITION_FAILED)
    else:
        userName = name
        data[userName] = {}
        passwords[userName] = str(request.json['pwd'])
        return jsonify(), OK


#  SHOW ALL
@app.route('/product', methods=['GET'])
def show_all_products():
    if userName == "":
        abort(UNAUTHORIZED)
    return jsonify(**(data[userName]))


#  DELETE
@app.route('/product', methods=['DELETE'])
def delete_product():
    if userName == "":
        abort(UNAUTHORIZED)
    if (not request.json) or ('name' not in request.json):
        abort(BAD_REQUEST)

    product = str(request.json['name'])

    if product in data[userName].keys():
        data[userName].pop(product)
        save_data()
        return jsonify(), OK
    else:
        abort(PRECONDITION_FAILED)


#  ADD
@app.route('/product', methods=['POST'])
def add_product():
    if userName == "":
        abort(UNAUTHORIZED)
    if (not request.json) or ('name' not in request.json):
        abort(BAD_REQUEST)

    product = str(request.json['name'])

    if product in data[userName].keys():
        abort(PRECONDITION_FAILED)

    else:
        data[userName][product] = 0
        save_data()
        return jsonify(), OK


#  CHANGE
@app.route('/product', methods=['PUT'])
def change_product():
    if userName == "":
        abort(UNAUTHORIZED)
    if (not request.json) or ('name' not in request.json) \
            or ('change' not in request.json) or (not is_int(request.json['change'])):
        abort(BAD_REQUEST)

    product = str(request.json['name'])
    change = int(request.json['change'])

    if product in data[userName].keys():
        quantity = int(data[userName][product])
        quantity += change

        if quantity < 0:
            abort(NOT_ACCEPTABLE)

        data[userName][product] = str(quantity)
        save_data()
        return jsonify(name=product, value=data[userName][product]), OK

    else:
        abort(PRECONDITION_FAILED)

if __name__ == '__main__':
    load_data()
    app.run(host='0.0.0.0', port=5678, debug=debug)
