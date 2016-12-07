from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select,WebDriverWait
from common_func import *
from entity import *
from entity import *
import time
import uuid,requests
from elasticsearch import Elasticsearch

success = 0
fail = 0
all_process = 13

def browser_Dri(url):
    browser = webdriver.Firefox()#浏览器的操作
    browser.get(url)
    return browser

def query_bill(host,params):
    print(params)
    en_param = url_encode(params)
    url_temp = host + '/rest/bills?para=' + en_param
    query_res = requests.get(url_temp)

    if query_res.status_code==200:
        query_res = query_res.json()
        print(query_res)
    return query_res["bills"]
def webhook_query(bill_no):
    es = Elasticsearch([{'host': '123.57.70.199', 'port': 9200}])
    dat1 = str(time.strftime("%Y.%m.%d", time.localtime(time.time())))
    search_index = "customer-info-webhook-" + dat1
    webhook_res = es.search(index=search_index, q='request_body:' + bill_no)
    return webhook_res

def status_query(host,params):
    temp_url=host+'/rest/offline/bill/status'
    for j in range(0,6):
        resp = request_post(temp_url,params)
        time.sleep(2)
    return resp
    #加判断成功失败

def repeat_query_bill(fp,host,query_bill_para, channel):
    query_bill_res = query_bill(host, query_bill_para)
    # print("bills:%r" % query_bill_res)
    for n in range(0,30):
        if query_bill_res == []:
            query_bill_res = query_bill(host, query_bill_para)
            # print("bills is empty")
            time.sleep(2)
        else:
            break
    if query_bill_res == [] :
        fail++
        print("----- Failed: bill insert fail " + channel)
        print("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------")
        fp.write("----- Failed bill insert:" + channel + "\n" )
        fp.write("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------\n")
        return 0
    

    spay_result = query_bill_res[0]["spay_result"]
    for m in range(0,60):
        if spay_result != True:
            query_bill_res = query_bill(host, query_bill_para)
            spay_result = query_bill_res[0]["spay_result"]
            # print("bills:%r" % spay_result)
            time.sleep(2)
        else:
            break
    if spay_result==True:
        fp.write("----- log: spay_result is true    \n")
        return 1
    else:
        fail++
        print("----- Failed: bill insert fail " + channel)
        print("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------")
        fp.write("----- Failed bill insert:" + channel + "\n" )
        fp.write("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------\n")
        return 0

def repeat_query_webhook(fp,bill_no,channel):
    webhook_res = webhook_query(bill_no)
    for i in range(0, 30):
        webhook_res_str = str(webhook_res)
        if "'reponse_body': 'success'" in webhook_res_str:
            success++
            print("----- log: webhook success" + channel + "pass")
            print("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------")
            fp.write("----- log: webhook success" + channel + "pass\n")
            fp.write("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------\n")
            break
        else:
            webhook_res = webhook_query(bill_no)
            time.sleep(5)
    if "'reponse_body': 'success'" not in webhook_res_str:
        fail++
        print("----- Failed: success not in webhook's response" + channel)
        print("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------")
        fp.write("----- Failed: success not in webhook's response" + channel + "\n" )
        fp.write("---------------success:" + success + "/" + all_process + "-----------fail:" + fail + "/" + all_process + "-------------\n")
        return 0
if __name__=="__main__":
    file_name = "E:\python learning\\auto_api_test\\auto_api_log.txt"
    fp = open(file_name, 'a+')
    tt=int(time.time())*1000
    host=url.url_8271_domain
    browser = browser_Dri("http://localhost:5002/")
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    # file_name = "E:\python learning\\api-test\Result\Result" + str(int(time.time())) + ".txt"
    browser.find_element_by_id("get_app_submit").click()
    for n in range(1,2):
        sel_app = Select(browser.find_element_by_id("app_select"))
        if n == 0:
            sel_app.select_by_visible_text("梦飞Test")
        if n == 1:
            sel_app.select_by_visible_text("线下服务商")
            browser.find_element_by_id("agent1").click()
        sel_parentChannel = Select(browser.find_element_by_id("parent_channel"))
        app_id = browser.find_element_by_id("app_id").get_attribute("value")
        print(app_id)
        app_secret = browser.find_element_by_id("app_secret").get_attribute("value")
        sign = sign_md5(app_id+str(tt)+app_secret)
        query_bill_para={
            "app_id":app_id,
            "app_sign":sign,
            "timestamp":tt
        }
        if n == 0:
            parentChannel_l=['BC','ALI','WX','UN']
        else:
            parentChannel_l = ['WX']
        # parentChannel_l = ['ALI']
        channel = {
            'BC': ['BC_WX_SCAN','BC_ALI_QRCODE','BC_ALI_SCAN','BC_EXPRESS'],
            'ALI': ['ALI_WEB', 'ALI_WAP', 'ALI_QRCODE', 'ALI_OFFLINE_QRCODE', 'ALI_SCAN'],
            'WX': ['WX_NATIVE','WX_SCAN'],
            'UN': ['UN_WEB', 'UN_WAP']}
        # channel = {
        #     'BC': ['BC_NATIVE','BC_WX_SCAN','BC_ALI_QRCODE','BC_ALI_SCAN','BC_EXPRESS'],
        #     'ALI': ['ALI_WEB', 'ALI_WAP', 'ALI_QRCODE', 'ALI_OFFLINE_QRCODE', 'ALI_SCAN'],
        #     'WX': ['WX_NATIVE', 'WX_SCAN'],
        #     'UN': ['UN_WEB', 'UN_WAP']}
        for p_ch in parentChannel_l:
            sel_parentChannel.select_by_value(p_ch)
            time.sleep(2)
            sel_channel = Select(browser.find_element_by_id("channel"))
            for s_ch in channel[p_ch]:
                bill_no = str(uuid.uuid1()).replace('-','')
                bill_no_ele = browser.find_element_by_id("bill_no")
                bill_no_ele.clear()
                bill_no_ele.send_keys(bill_no)
                query_bill_para["bill_no"]=bill_no
                query_bill_para["channel"]=s_ch
                print(bill_no)
                sel_channel.select_by_value(s_ch)
                fp.write(bill_no + ":/n")
                fp.write(s_ch)
                if s_ch=="BC_WX_SCAN" or s_ch == "BC_ALI_SCAN" or s_ch == "ALI_SCAN" or s_ch == "WX_SCAN":
                    auth_code = input(s_ch+"'s auth_code:")
                    browser.find_element_by_id("auth_code").clear()
                    browser.find_element_by_id("auth_code").send_keys(auth_code)
                time.sleep(2)
                browser.find_element_by_id("lala").click()
                time.sleep(2)
                if s_ch == "BC_WX_SCAN" or s_ch == "BC_ALI_SCAN" or s_ch == "ALI_SCAN" or s_ch == "WX_SCAN":
                    status_query(host,query_bill_para)
                if repeat_query_bill(fp,host,query_bill_para) == 1 :
                    repeat_query_webhook(fp,bill_no,s_ch)





    fp.close()
    browser.quit()




