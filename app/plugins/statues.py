from flask import Blueprint, jsonify, request
from flask import render_template
import pymongo
import json
from app import utilities

st_bp = Blueprint("st", __name__)


@st_bp.route('/')
def status():
    return render_template("statues.html")


@st_bp.route('/logs', methods=['GET'])
def logfile():
    offset = int(request.args.get("offset"))
    limit = int(request.args.get("limit"))
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    total_size = mydb.command("collstats", "log")["count"]
    mycol = mydb["log"]
    data = [item for item in mycol.find(None).sort([("_id", -1)]).skip(offset).limit(limit)]
    for its in data:
        del its["_id"]
        if its["status"] == 'Done':
            its["status"] = '<span style=color:green;font-weight:bold>'+ its["status"] +'</span>'
        else:
            its["status"] = '<span style=color:blue;font-weight:bold>'+ its["status"] +'</span>'
    return jsonify(json.loads(str({
        "total": total_size,
        "rows": data
    }).replace("'", '"')))

if __name__ == '__main__':
    logfile(0)