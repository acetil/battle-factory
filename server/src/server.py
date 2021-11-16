import sys
from flask import Flask, request
from flask_cors import CORS

from json import dumps

from werkzeug.exceptions import HTTPException

from usage_scraping import getRandom, getUsage

def defaultHandler (err):
    response = err.get_response()
    print('response', err, err.get_response())
    response.data = dumps({
        "code": err.code,
        "name": "System Error",
        "message": err.get_description(),
    })
    response.content_type = 'application/json'
    return response

APP = Flask(__name__)
CORS(APP)

APP.config["TRAP_HTTP_EXCEPTIONS"] = True
APP.register_error_handler(HTTPException, defaultHandler)

@APP.route("/api/test/usage", methods=["GET"])
def http_getUsage ():
    tier = request.args.get("tier", type=str)
    species = request.args.get("species", type=str)

    return dumps(getUsage(tier, species), indent=4, sort_keys=True)

@APP.route("/api/test/pokemon", methods=["GET"])
def http_randomPokemon ():
    tier = request.args.get("tier", type=str)
    species = request.args.get("species", None, type=str)

    return dumps(getRandom(tier, species))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    APP.run(port=port, debug=True)