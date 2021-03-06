from flask import Flask, request, send_from_directory, render_template
from api_parser import *
from api_checkers import log_and_check_params
from api_conf import server_url, listen_port, listen_host, debug, ssl_verify
from time import strftime
from datetime import timedelta, date
from html import parser
import json
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(filename=".api.log", level=logging.INFO)

def track_event(category, action, label=None, value=0):
    data = {
        'v': '1',  # API Version.
        'tid': 'UA-96333689-1',  # Tracking ID / Property ID.
        'cid': '555',
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
    }
    response = requests.post(
        'http://www.google-analytics.com/collect', data=data)
    response.raise_for_status()

@app.route('/', methods=['POST', 'GET'])
def doc():
    track_event(category='Doc', action=request.method)
    return render_template("epinoob_api_doc.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    track_event(category='Login', action=request.method)
    error, session, params = log_and_check_params(["login", "password"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    return json.dumps({"token":session.cookies['user']})

@app.route('/infos', methods=['POST', 'GET'])
def infos():
    """/login   (POST,GET) login, password"""
    track_event(category='Infos', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/?format=json", verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return r.text
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect through Epitech API", "code": 500}}), 500

@app.route('/planning', methods=['POST', 'GET'])
def planning():
    """/planning    (POST,GET) login, password, start, end, [get] (all, registered, free)"""
    track_event(category='Planning', action=request.method)
    error, session, params = log_and_check_params(["start", "end", "token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    if "get" in params.keys():
        get = params['get']
    else:
        get = "all"
    start = params['start']
    end = params['end']
    try:
        r = session.post(server_url+"/intra/planning/load?format=json&start=%s&end=%s" % (start, end), verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        if debug:
            log_file("Intra replied in %s seconds" %r.elapsed)
        if len(r.text) < 2:
            return (json.dumps({"error":{"message":"Epitech API returned an empty response", "code":500}})), 500
        planning = json.loads(r.text)
        filtered_planning = get_classes_by_status(planning, get)
        return json.dumps(filtered_planning)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/susies', methods=['POST', 'GET'])
def susies():
    track_event(category='Susies', action=request.method)
    error, session, params = log_and_check_params( ["start", "end", "token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    if "get" in params.keys():
        get = params['get']
    else:
        get = "all"
    start = params['start']
    end = params['end']
    try:
        r = session.post(server_url+"/intra/planning/load?format=json&start=%s&end=%s" % (start, end), verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        if len(r.text) < 2:
            return json.dumps({"error":{"message":"Intra replied an empty string. Please check your date format"}})
        planning = json.loads(clean_json(r.text))
        susies = get_classes_by_calendar_type(planning, 'susie')
        susies = get_classes_by_status(susies, get)
        return json.dumps(susies)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/susie', methods=['POST', 'GET', 'DELETE'])
def susie(action=""):
    track_event(category='Susies', action=request.method)
    method = request.method
    error, session, params = log_and_check_params(["id", "token", "calendar_id"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    _id = params['id']
    try:
        if method == "POST":
            r = session.post(server_url+"/planning/%s/%s/subscribe?format=json" % (params['calendar_id'],_id), verify=ssl_verify)
        elif method == "DELETE":
            r = session.post(server_url+"/planning/%s/%s/unsubscribe?format=json" % (params['calendar_id'],_id), verify=ssl_verify)
        elif method == "GET":
            r = session.post(server_url+"/planning/%s/%s/?format=json" % (params['calendar_id'], _id), verify=ssl_verify)
        if r.status_code == 403:
            if "// Epitech JSON webservice" in r.text:
                return clean_json(r.text), 403
            else:
                return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/projects', methods=['POST', 'GET'])
def projects():
    """/projects  (POST,GET) login, password, [get]"""
    track_event(category='Projects', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    if "get" in params.keys():
        get = params['get']
    else:
        get = "all"
    d = date.today()
    start = strftime("%Y-%m-%d", d.timetuple())
    d = date.today() + timedelta(days=365);
    end = strftime("%Y-%m-%d", d.timetuple())
    if "end" in params.keys():
        end = params["key"]
    try:
        r = session.post(server_url+"/module/board/?format=json&start=%s&end=%s" % (start, end),verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        projects = json.loads(r.text)
        projects = filter_projects(projects, get)
        return json.dumps(projects)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/project', methods=['GET', 'POST', 'DELETE'])
def project():
    track_event(category='Project', action=request.method)
    method = request.method
    error, session, params = log_and_check_params(["token", "scolaryear", "codemodule", "codeinstance", "codeacti"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        if method == "GET":
            r = session.post(server_url+"/module/%s/%s/%s/%s/project/?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti']), verify=ssl_verify)
        elif method == "POST":
            r = session.post(server_url+"/module/%s/%s/%s/%s/project/register?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti']), verify=ssl_verify)
        elif method == "DELETE":
            r = session.post(server_url+"/module/%s/%s/%s/%s/project/destroygroup?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti']), verify=ssl_verify)
        if r.status_code == 403:
            if "// Epitech JSON webservice" in r.text:
                return clean_json(r.text), 403
            else:
                return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 50
0
@app.route('/project/files' ,methods=['GET'])
def get_file():
    track_event(category='Project/Files', action=request.method)
    method = request.method
    error, session, params = log_and_check_params(["token", "scolaryear", "codemodule", "codeinstance", "codeacti"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/module/%s/%s/%s/%s/project/file/?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti']), verify=ssl_verify )
        if r.status_code == 403:
            if "// Epitech JSON webservice" in r.text:
                return clean_json(r.text), 403
            else:
                return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/allmodules', methods=['GET'])
def allmodules():
    track_event(category='AllModules', action=request.method)
    error, session, params = log_and_check_params(["token", "scolaryear", "location", "course"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.get(server_url+"/course/filter?format=json&preload=1&location=FR&location=%s&course=%s&scolaryear=%s" %(params['location'], params['course'], params['scolaryear']), verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect through Epitech API", "code": 500}}), 500

@app.route('/modules', methods=['POST', 'GET'])
def modules():
    """/modules (POST,GET) login, password"""
    track_event(category='Modules', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.get(server_url+"/user/#!/netsoul", verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return get_modules(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect through Epitech API", "code": 500}}), 500

@app.route('/module', methods=['GET', 'POST', 'DELETE'])
def module():
    track_event(category='Module', action=request.method)
    method = request.method
    error, session, params = log_and_check_params(["token", "scolaryear", "codemodule", "codeinstance"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        if method == "GET":
            url = server_url+"/module/%s/%s/%s/?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'])
        if method == "POST":
            url = server_url+"/module/%s/%s/%s/register?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'])
        if method == "DELETE":
            url = server_url+"/module/%s/%s/%s/unregister?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'])
        r = session.post(url, verify=ssl_verify)
        if r.status_code == 403:
            if "// Epitech JSON webservice" in r.text:
                return clean_json(r.text), 403
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect to Epitech's intra API", "code": 500}}), 500

@app.route('/marks', methods=['POST', 'GET'])
def marks():
    """/marks (POST,GET) login, password"""
    track_event(category='Marks', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/user/#!/netsoul", verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return get_marks(r.text)
    except:
        return {"error": {"message": "Server was unable to connect through Epitech API", "code": 500}}

@app.route('/messages', methods=['POST', 'GET'])
def messages():
    """/messages (POST,GET) login, password"""
    track_event(category='Messages', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/intra/user/notification/message?format=json", verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/alerts', methods=['POST', 'GET'])
def alerts():
    """/alerts (POST,GET) login, password"""
    track_event(category='Alerts', action=request.method)
    error, session, params = log_and_check_params(["token"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/intra/user/notification/alert?format=json", verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error":{"message":str(e), "code":500}}), 500

@app.route('/photo', methods=['POST', 'GET'])
def photo():
    """/photo (POST,GET) login, password"""
    track_event(category='Photo', action=request.method)
    error, session, params = log_and_check_params(["token", "login"], request)
    if error != {}:
        return json.dumps(error)
    return json.dumps({"url": "https://cdn.local.epitech.eu/userprofil/profilview/%s.jpg" %params['login']})


@app.route('/token', methods=['POST', 'GET'])
def token():
    """/token (POST,GET) login, password, scolaryear, codemodule, codeinstance, codeacti, token"""
    track_event(category='Token', action=request.method)
    error, session, params = log_and_check_params(["tokenvalidationcode", "scolaryear", "codemodule", "codeinstance", "codeacti", "token", "codeevent"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        payload = {'token': params['tokenvalidationcode'], 'rate': 1, 'comment': ''}
        url = server_url+"/module/%s/%s/%s/%s/%s/token?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti'], params['codeevent'])
        r = session.post(url, data=payload, verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect to Epitech's intra API", "code": 500}}), 500

@app.route('/user', methods=['GET'])
def user():
    track_event(category='User', action=request.method)
    error, session, params = log_and_check_params(["token", "user"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        r = session.post(server_url+"/user/%s?format=json" %params['user'], verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect to Epitech's intra API", "code": 500}}), 500

@app.route('/event', methods=['GET', 'POST', 'DELETE'])
def event():
    track_event(category='Event', action=request.method)
    method = request.method
    error, session, params = log_and_check_params(["token", "scolaryear", "codemodule", "codeinstance", "codeacti", "codeevent"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        if method == "GET":
            url = server_url+"/module/%s/%s/%s/%s/%s/?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti'], params['codeevent'])
        if method == "POST":
            url = server_url+"/module/%s/%s/%s/%s/%s/register?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti'], params['codeevent'])
        if method == "DELETE":
            url = server_url+"/module/%s/%s/%s/%s/%s/unregister?format=json" % (params['scolaryear'], params['codemodule'], params['codeinstance'], params['codeacti'], params['codeevent'])
        r = session.post(url, verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect to Epitech's intra API", "code": 500}}), 500

@app.route('/trombi', methods=['GET'])
def trombi():
    track_event(category='Trombi', action=request.method)
    h = parser.HTMLParser()
    filters = ""
    method = request.method
    error, session, params = log_and_check_params(["token", "location", "year"], request)
    if error != {}:
        return json.dumps(error), error['error']['code']
    try:
        for param in params:
            if param != "login" and param != "password":
                filters = filters + "&%s=%s" % (param, params[param])
        r = session.post(server_url+"/user/filter/user?format=json"+filters, verify=ssl_verify)
        if r.status_code == 403:
            return json.dumps({"error": {"message": "Connection token is invalid or has expired", 'code':403}}), 403
        return clean_json(r.text)
    except Exception as e:
        return json.dumps({"error": {"message": "Server was unable to connect to Epitech's intra API", "code": 500}}), 500

@app.route('/favicon.ico', methods=['POST', 'GET'])
def favicon():
    track_event(category='Favicon', action=request.method)
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/wakeup', methods=['POST', 'GET'])
def wake_up():
    track_event(category='WakeUp', action=request.method)
    return ("OK")

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add("Access-Control-Allow-Methods", "POST, GET, PUT, OPTIONS, PATCH, DELETE")
    response.headers.add('Access-Control-Allow-Headers',"Origin, X-Requested-With, Content-Type, Accept")
    response.headers.add('Content-Type','application/json')
    return response

if __name__ == '__main__':
    try:
        app.debug = debug
        app.run(port=listen_port, host=listen_host, threaded=True)
    except Exception as e:
        if debug:
            log_file(e)
