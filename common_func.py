import requests,urllib,json,hashlib


def request_post(url,params):
    # print(url)
    jdata = json.dumps(params)
    # print(jdata)
    #r1 = requests.get('http://en.wikipedia.org/wiki/Monty_Python')
    try:
        r=requests.post(url,json=params)
        #print(r.status_code)
    except requests.exceptions.HTTPError:
        return "httperror"
    # print(r.status_code)
    if r.status_code==200:
         # print('common function200')
         resp=r.json()
         # common_func.print_resp(resp)
         return resp
    else:
        # print('common_func'+str(r.status_code))
        # r=r.json()
        return r
        # return r.status_code
def request_get(url):
    param1={"type":"C"}
    param2=json.dumps(param1)
    param=urllib.parse.quote_plus(param2)
    url=url+'?para='+param
    print(url)
    resp_get = requests.get(url)
    resp = resp_get.json()
    return resp
def request_delete(url,param):
    resp = requests.delete(url,params=param)
    if resp.status_code ==200:
        cancel_resp = resp.json()
        # common_func.print_resp(cancel_subs_resp)
        return cancel_resp
    else:
        return resp
def request_put(url,param):
    resp = requests.put(url,json = param)
    put_resp = resp.json()
    # common_func.print_resp(cancel_subs_resp)
    if resp.status_code ==200:
        put_resp = resp.json()
        # common_func.print_resp(cancel_subs_resp)
        return put_resp
    else:
        return resp

def sign_md5(str1):
    m=hashlib.md5()
    m.update(str1.encode('utf-8'))
    get_md5= m.hexdigest()
    return get_md5

def print_resp(resp):
    dict={'name':'python','english':33,'math':35}
    l=[]
    if type(l) is type(resp):
        for r in resp:
            if type(r) is type(dict):
                for i in r:
                    print("%s:%s"%(i,r[i]))
            else:
                print(resp)
    else:
        if type(resp) is type(dict):
                for i in resp:
                    print("%s:%s"%(i,resp[i]))
        else:
            print(resp)

def url_encode(paramm):
    param1=paramm
    param2=json.dumps(param1)
    param=urllib.parse.quote_plus(param2)
    return param

def attachAppSign(reqPara,bcapp):
    bcapp.app_id

