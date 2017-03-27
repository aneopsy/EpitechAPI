import time

def log_file(msg, code=0):
    date = time.strftime("[%d/%m/%Y %H:%m:%S]");
    with open("api.log", "a+") as f:
        f.write("%s :[%s]%s\n" %(date, code, msg))
        f.close()

def clean_json(json_raw):
    return json_raw

def epur(json_raw):
    return json_raw.replace("\t", "").replace("\n", "")

def get_classes_by_calendar_type(planning, type):
    output = []
    for item in planning:
        if hasattr(item, "keys"):
            if "calendar_type" in item.keys():
                if item['calendar_type'] == type:
                    output.append(item)
    return output

def get_classes_by_status(planning, status):
    filters = status.split("|")
    if "all" in filters:
        return planning
    output = planning
    for _filter in filters:
        if _filter not in ["registered", "free"]:
            return {"error":{"message":"Invalid filter : %s" % _filter, "code":400}}
        for item in output:
            if _filter == "registered":
                if hasattr(item, "keys"):
                    if "event_registered" not in item.keys() or item['event_registered'] == 'null' or item['event_registered'] is None:
                        output.pop(output.index(item))
            elif _filter == "free":
                if hasattr(item, "keys"):
                    if "registered" not in item.keys() or "nb_place" not in item.keys():
                        output.pop(output.index(item))
                    elif item["nb_place"] <= item["registered"]:
                        output.pop(output.index(item))
            else:
                return {"error":{"message":"Invalid filter : %s" % _filter, "code":400}}
    return output

def filter_projects(planning, filters):
    filters = filters.split("|")
    output = []
    for _filter in filters:
        for project in planning:
            if _filter == "registered":
                if project["registered"] != 0:
                    output.append(project)
            elif _filter == "all":
                output.append(project)
    return output

def get_parameters(method, request):
    if method == 'POST':
        return request.form
    elif method == 'GET':
        if (len(request.args) == 0):
            return request.form
        else:
            return request.args
    else:
        if (len(request.args) == 0):
            return request.form
        else:
            return request.args

def get_marks(html_raw):
    pos = html_raw.find('notes: [')
    pos2 = html_raw.find('});', pos)
    output = html_raw[pos:pos2 + 1]
    return "{"+output

def get_modules(html_raw):
    haystack = "window.user = $.extend(window.user || {}, {"
    pos = html_raw.find(haystack)
    pos2 = html_raw.find("notes: [")
    return "{"+html_raw[pos+len(haystack):pos2 -4]+"}"
