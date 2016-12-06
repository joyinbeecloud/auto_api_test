from logging import NullHandler
from common_func import *
from entity import *
import json,time
import uuid
from flask import Flask, request, redirect, render_template,Markup
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host':'123.57.70.199','port':9200}])

app = Flask(__name__)
file_name = "E:\python learning\\auto_api_test\\auto_api_log.txt"
fp = open(file_name,'a+')

@app.route('/')
def hello_index():
    return app.send_static_file("index.html")

@app.route('/bill',methods=['post','GET'])
def bill():
    print(111)
    app_id = beecloud_app.e66_appID  # 'ed777f93-0c4a-4bc4-b7b3-6573d6da48df'
    app_secret = beecloud_app.e66_appSecret
    channel_list=['BC_WX_WAP',
                  'BC_NATIVE',
                  'BC_WX_SCAN',
                  'BC_ALI_QRCODE',
                  'BC_ALI_SCAN',
                  'BC_EXPRESS',
                  'ALI_WEB',
                  'ALI_WAP',
                  'ALI_QRCODE',
                  'ALI_OFFLINE_QRCODE',
                  'ALI_SCAN',
                  'WX_NATIVE',
                  'WX_SCAN',
                  'UN_WEB',
                  'UN_WAP']
    url=request.form['host']
    tt = int(time.time()) * 1000
    dat = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
    dat1 = str(time.strftime("%Y.%m.%d", time.localtime(time.time())))
    search_index = "customer-info-webhook-" + dat1

    print("执行时间" + dat)
    sign = sign_md5(app_id + str(tt) + app_secret)
    online_bill_values = {
        'app_id': app_id,
        'timestamp': tt,
        'app_sign': sign,
        # ali_web,un_web    CP_WEB  BC_WX_WAP  BC_ALI_QRCODE(url里不加offline)  BC_ALI_SCAN和BC_WX_SCAN是线下的（url加offline）_
        'title': 'BeeCloud 渠道测试',  # title过长时不传值到提示信息里
        'total_fee': 1,  # 2000000000  WX_NATIVE 渠道方错误 invalid total_fee  最大1000w
        'bill_no': '201612050001',
        'return_url': 'http://beecloud.cn',
        'optional': {"aa":"bb"},
    }
    for channel in channel_list:

        bill_no = str(uuid.uuid1()).replace('-', '')
        fp.write(bill_no + ':')
        online_bill_values["bill_no"]=bill_no
        online_bill_values["channel"]=channel
        if channel == 'BC_ALI_SCAN' or channel == 'BC_WX_SCAN' or channel == 'WX_SCAN' or channel == 'ALI_SCAN' or channel == 'ALI_OFFLINE_QRCODE':
            url_temp = url+"/rest/offline/bill"
        else:
            url_temp = url+"/rest/bill"
        print(url_temp)
        resp = request_post(url_temp, online_bill_values)

        deal_with_pay(channel, resp, online_bill_values["total_fee"])

        if "id" in resp.keys():
            id = resp["id"]
            en_param = common_func.url_encode(online_bill_values)
            url_temp1 = url+'/rest/bill/' + id + '?para=' + en_param
            resp_get = requests.get(url_temp1)
            while resp_get["spay_result"] != True:
                resp_get = requests.get(url_temp1)
            webhook_res = es.search(index=search_index, q='request_body:' + bill_no)
            for i in range(0,5):
                webhook_res_str = str(webhook_res)
                if "'reponse_body': 'success'" in webhook_res_str:
                    break
                else:
                    webhook_res = es.search(index=search_index, q='request_body:' + bill_no)
                    time.sleep(5)
        else:
            print("bill接口返回的内容里不包含id")
            fp.write("bill接口返回的内容里不包含id")





fp.close()





def deal_with_pay(channel,resp,total_fee):
    if channel == 'BC_WX_WAP':
        if 'url' in resp.keys():
            word = u'微信wap的返回数据，把以下的url在手机端的非微信浏览器打开即可支付'
            return render_template('show_url.html', word = word,result=resp,url=resp['url'],id=resp['id'],err_detail=resp['err_detail'].encode('utf-8'))
        else:
            return render_template('show_url.html', result=resp,err_detail=resp['err_detail'],result_code=resp['result_code'])

    elif channel == 'BC_NATIVE' or channel == 'BC_ALI_QRCODE' or channel == 'ALI_OFFLINE_QRCODE' or channel == 'WX_NATIVE':
        if 'code_url' in resp.keys():
            if resp['code_url'] !='' and resp['result_code'] == 0:
                return render_template('qrcode.html', raw_content=resp['code_url'], total_fee=total_fee)
            else:
                return render_template('show_url.html', err_detail=resp['err_detail'],result_code=resp['result_code'])
        else:
            return render_template('show_url.html', err_detail=resp['err_detail'],result_code=resp['result_code'])
    elif channel == 'ALI_WEB' or channel == 'ALI_WAP' or channel =='ALI_QRCODE':
        if 'url' in resp.keys():
            if resp['url'] != '' and resp['result_code'] == 0:
                return redirect(resp['url'])
            else:
                return render_template('show_url.html', err_detail=resp['err_detail'],result_code=resp['result_code'])
        else:
            return render_template('show_url.html', err_detail=resp['err_detail'],result_code=resp['result_code'])
    elif channel == 'BC_WX_SCAN' or channel == 'BC_ALI_SCAN' or channel == 'ALI_SCAN' or channel == 'WX_SCAN':
        if resp['result_code']==0 and resp['pay_result']==True:
            return app.send_static_file('success.html')
        else:
            return render_template('show_url.html',err_detail=resp['err_detail'],result_code=resp['result_code'])
    elif channel == 'BC_EXPRESS' or channel == 'UN_WEB' or channel == 'UN_WAP':
        if resp['result_code'] == 0 and resp['html'] != '':
            return render_template('blank.html',content=Markup(resp['html']))
        else:
            return render_template('show_url.html',err_detail=resp['err_detail'],result_code=resp['result_code'])


if __name__ == '__main__':
    app.run()

