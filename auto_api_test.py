import webbrowser

from common_func import *
from entity import *
import gl
import time
import uuid,requests
from elasticsearch import Elasticsearch

def query_bill(host,params):
    tt = int(time.time()) * 1000
    params['timestamp'] = tt
    params['app_sign'] = sign_md5(params['app_id']+str(tt)+params['app_secret'])
    # print(params)
    # if params['channel'] == 'BC_ALI_WAP' or params['channel'] == 'BC_ALI_APP':
    #     params['channel'] = None
    en_param = url_encode(params)
    url_temp = host + '/rest/bills?para=' + en_param
    try:
        query_res = requests.get(url_temp)
    except requests.exceptions.ConnectTimeout:
        fp.write('bills timeout')
        print('bills timeout')
    print("query_bills_res:%r"%query_res.json())
    if query_res.status_code==200:
        query_res = query_res.json()
        if 'bills' in query_res.keys():
            return query_res["bills"]
        else:
            return query_res
    else:
        return query_res

def webhook_query(bill_no):
    es = Elasticsearch([{'host': '123.57.70.199', 'port': 9200}])
    dat1 = str(time.strftime("%Y.%m.%d", time.localtime(time.time())))
    search_index = "customer-info-webhook-" + dat1
    webhook_res = es.search(index=search_index, q='request_body:' + bill_no, request_timeout=60)
    print('webhook query:%r' % webhook_res)
    return webhook_res


def status_query(host, params, channel, isAgent):
    print('status query')
    tt = int(time.time()) * 1000
    params['timestamp'] = tt
    params['app_sign'] = sign_md5(params['app_id'] + str(tt) + params['app_secret'])
    if isAgent:
        temp_url = host + '/rest/offline/agent/bill/status'
    else:
        temp_url = host + '/rest/offline/bill/status'
    for j in range(0, 15):
        resp = request_post(temp_url, params)
        time.sleep(1)
    if 'pay_result' in resp.keys():
        if resp['pay_result'] == True:
            fp.write("----- log: %r's bill status,pay_result is true    \n" % channel)
            print("%r's bill status true" % channel)
            return 1
        else:
            gl.fail += 1
            fp.write("----- log: %r's bill status,pay_result is false    \n" % channel)
            fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
            gl.success, gl.all_process, gl.fail, gl.all_process))
            gl.fail_channel.append(channel)
            print("%r's bill status false" % channel)
            return 0
    else:
        gl.fail += 1
        fp.write("----- log: %r bill status fail  \n" % channel)
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append(channel)
        print("%r's bill status fail" % channel)
        return 0



        # 加判断成功失败 已加


def repeat_query_bill(fp, host, query_bill_para, channel):
    query_bill_res = query_bill(host, query_bill_para)
    # print("bills:%r" % query_bill_res)
    for n in range(0, 180):
        if query_bill_res == []:
            query_bill_res = query_bill(host, query_bill_para)
            # print("bills is empty")
            time.sleep(1)
        else:
            break
    if query_bill_res == []:
        gl.fail += 1
        print("----- Failed: bill insert fail " + channel)
        print("---------------success: %r/%r-----------fail:%r/%r-------------" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        fp.write("----- Failed bill insert:" + channel + "\n")
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append(channel)
        return 0

    spay_result = query_bill_res[0]["spay_result"]
    for m in range(0, 180):
        if spay_result != True:
            query_bill_res = query_bill(host, query_bill_para)
            spay_result = query_bill_res[0]["spay_result"]
            print("bills:%r" % spay_result)
            time.sleep(1)
        else:
            break
    if spay_result == True:
        fp.write("----- log: spay_result is true    \n")
        return 1
    else:
        gl.fail += 1
        print("----- Failed: bill insert fail " + channel)
        print("---------------success:%r/%r-----------fail:%r/%r-------------" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        fp.write("----- Failed bill insert:" + channel + "\n")
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append(channel)
        return 0


def repeat_query_webhook(fp, bill_no, channel):
    webhook_res = webhook_query(bill_no)
    for i in range(0, 120):
        webhook_res_str = str(webhook_res)
        if "'reponse_body': 'success'" in webhook_res_str:
            gl.success += 1
            print("----- log: webhook success " + channel + " pass")
            print("---------------success:%r/%r-----------fail:%r/%r-------------" % (
            gl.success, gl.all_process, gl.fail, gl.all_process))
            fp.write("----- log: webhook success " + channel + " pass\n")
            fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
            gl.success, gl.all_process, gl.fail, gl.all_process))
            break
        else:
            webhook_res = webhook_query(bill_no)
            time.sleep(2)
    if "'reponse_body': 'success'" not in webhook_res_str:
        gl.fail += 1
        print("----- Failed: success not in webhook's response " + channel)
        print("---------------success:%r/%r-----------fail:%r/%r-------------" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        fp.write("----- Failed: success not in webhook's response " + channel + "\n")
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append(channel)
        return 0


def transfer_req(url, channel, params):
    bill_no = str(uuid.uuid1()).replace('-', '')
    fp.write(bill_no + ':' + channel)
    if channel == 'wx_transfer' or channel == 'ali_transfer':
        params['transfer_no'] = bill_no
        url_temp = url + '/rest/transfer'
        resp = common_func.request_post(url_temp, params)
    else:
        params['bill_no'] = bill_no
        url_temp = url + '/rest/bc_transfer'
        resp = common_func.request_post(url_temp, params)
    print(channel + '打款返回内容')
    common_func.print_resp(resp)
    if resp['result_code'] == 0 and resp['result_msg'] == 'OK':
        # gl.success += 1
        print(channel + ': OK')
        fp.write('----- log:%s OK\n' % channel)
        if channel == 'ali_transfer':
            time.sleep(150)
        else:
            time.sleep(90)
        if channel != 'wx_transfer':
            print(bill_no)
            repeat_query_webhook(fp, bill_no, channel)
        else:
            gl.success += 1
            fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
                gl.success, gl.all_process, gl.fail, gl.all_process))

    else:
        gl.fail += 1
        print('打款失败')
        fp.write("----- Failed transfer:" + channel + "\n")
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append(channel)


def transfer(fp, host):
    app_id = gl.app_id
    app_secret = gl.app_secret
    tt = int(time.time()) * 1000
    sign = sign_md5(app_id + str(tt) + app_secret)
    channel = ['wx_transfer', 'ali_transfer']
    # channel=['bc_transfer','wx_transfer','ali_transfer']
    transfer_type = {
        'bc_transfer': {
            'app_id': app_id,
            'timestamp': tt,
            'app_sign': sign,
            'total_fee': 1,  # 测到这个
            # 'bill_no':'20160701'+str(int(time.time())),
            'title': '京东打款',
            'trade_source': 'OUT_PC',  # OUT_PC
            'card_type': 'DE',  # CR  DEC
            'account_type': 'P',  # P    C
            'bank_fullname': '交通银行',
            'account_no': '6222600170004441589',
            'account_name': '陈梦飞',
            'optional': {'test': 'test BeeCloud transfer'},
            'notify_url': 'http://www.baidu.com',
        },
        'wx_transfer': {
            'app_id': app_id,
            'timestamp': tt,
            'app_sign': sign,
            'total_fee': 101,  # 测到这个
            'channel': 'WX_TRANSFER',  # WX_REDPACK, WX_TRANSFER, ALI_TRANSFER
            # 'bill_no':'20160701'+str(int(time.time())),
            'title': 'BeeCloud打款测试',
            'desc': '微信打款',  # OUT_PC
            'channel_user_id': 'o3kKrjpGXh0hM-ysNdZEgHZpGFqM',
            # 821159330@qq.com   我 o3kKrjpGXh0hM-ysNdZEgHZpGFqM 钱o3kKrjobVuhf0cDGsyUSve8wYGhk   wenlong o3kKrjlUsMnv__cK5DYZMl0JoAkY
            'channel_user_name': '陈梦飞',
            'redpack_info': {},
            'account_name': '苏州比可网络科技有限公司',  # 苏州比可网络科技有限公司

        },
        'ali_transfer': {
            'app_id': app_id,
            'timestamp': tt,
            'app_sign': sign,
            'total_fee': 1,  # 测到这个
            'channel': 'ALI_TRANSFER',  # WX_REDPACK, WX_TRANSFER, ALI_TRANSFER
            # 'bill_no':'20160701'+str(int(time.time())),
            'title': 'BeeCloud打款测试',
            'desc': '支付宝打款',  # OUT_PC
            'channel_user_id': '821159330@qq.com',
            'channel_user_name': '陈梦飞',
            'redpack_info': {},
            'account_name': '苏州比可网络科技有限公司',  # 苏州比可网络科技有限公司

        },
    }

    print("执行时间" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))))
    for c in channel:
        trans_resp = transfer_req(host, c, transfer_type[c])


def auth(fp, host):
    app_id = gl.app_id  # test  #   c37d661d-7e61-49ea-96a5-68c34e83db3b
    app_secret = gl.app_secret
    tt = int(time.time()) * 1000
    sign = common_func.sign_md5(app_id + str(tt) + app_secret)

    auth_values1 = {
        'app_id': app_id,
        'timestamp': tt,
        'app_sign': sign,
        'name': '陈梦飞',
        'id_no': '330682198904063427',
        'card_no': '6217906101007446144',
        'mobile': '13575765971'
    }
    auth_values2 = {
        'app_id': app_id,
        'timestamp': tt,
        'app_sign': sign,
        'name': '陈梦',
        'id_no': '330682198904063427',
        'card_no': '6217906101007446144',
        # 'mobile': '13575765971'
    }
    url_temp1 = host + '/auth'
    resp = request_post(url_temp1, auth_values1)
    common_func.print_resp(resp)

    if resp['result_code'] == 0 and resp['result_msg'] == 'OK' and resp['auth_result'] == True:
        gl.success += 1
        print('auth OK')
        fp.write('----- log: 正确信息鉴权成功\n')
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))

    else:
        gl.fail += 1
        print('正确信息鉴权失败')
        fp.write("----- Failed auth:result_msg:%r,err_detail:%r\n" % (resp['result_msg'], resp['err_detail']))
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append('right info auth')
    resp1 = request_post(url_temp1, auth_values2)
    if resp1['result_code'] == 0 and resp1['result_msg'] == 'OK':
        if resp1['auth_msg'] == '亲，认证信息不一致' or resp1['auth_msg'] == '卡号姓名不匹配':
            gl.success += 1
            print('auth OK')
            fp.write('----- log: 错误信息鉴权成功\n')
            fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
                gl.success, gl.all_process, gl.fail, gl.all_process))

        else:
            gl.fail += 1
            print('错误信息鉴权失败')
            fp.write("----- 错误信息鉴权失败:result_msg:%r,err_detail:%r\n" % (resp['result_msg'], resp['err_detail']))
            fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
            gl.success, gl.all_process, gl.fail, gl.all_process))
            gl.fail_channel.append('error info auth')
    else:
        gl.fail += 1
        print('错误信息鉴权失败')
        fp.write("----- 错误信息鉴权失败:result_msg:%r,err_detail:%r\n" % (resp['result_msg'], resp['err_detail']))
        fp.write("---------------success:%r/%r-----------fail:%r/%r-------------\n" % (
        gl.success, gl.all_process, gl.fail, gl.all_process))
        gl.fail_channel.append('error info auth')

def deal_with_pay(channel,resp,fp):
    # print(resp)
    # print(channel)
    if channel == 'BC_NATIVE' or channel == 'BC_ALI_QRCODE' or channel == 'ALI_OFFLINE_QRCODE' or channel == 'WX_NATIVE' or channel == 'BC_ALI_WAP' or channel == 'BC_ALI_APP':
        if 'code_url' in resp.keys():
            if resp['code_url'] !='' and resp['result_code'] == 0:
                print(resp)
                webbrowser.open('https://cli.im/api/qrcode/code?text='+resp['code_url'])
            else:
                print(resp)
                fp.write(resp)
        else:
            print(resp)
            fp.write(resp)

    elif channel == 'ALI_WEB' or channel == 'ALI_WAP' or channel =='ALI_QRCODE':
        if 'url' in resp.keys():
            if resp['url'] != '' and resp['result_code'] == 0:
                webbrowser.open(resp['url'])

            else:
                print(resp)
                fp.write(resp)

        else:
            print(resp)
            fp.write(resp)

    elif channel == 'BC_WX_SCAN' or channel == 'BC_ALI_SCAN' or channel == 'ALI_SCAN' or channel == 'WX_SCAN':
        if resp['result_code']==0:
            if resp['pay_result']==True:
                print('pay successfully')
            else:
                print('waiting for password')
        else:
            print(resp)
    elif channel == 'BC_EXPRESS' or channel == 'UN_WEB' or channel == 'UN_WAP' or channel == 'JD_WEB':
        if 'html' in resp.keys():
            if resp['result_code'] == 0 and resp['html'] != '':
                print(resp)
                file_html_name = "D:\project\\auto_api_test\Result\\pay_web.html"
                fp_html = open(file_html_name,'w+')
                fp_html.write(resp['html'])
                fp_html.close()
                webbrowser.open(file_html_name)

            else:
                print(resp)
                fp.write(resp)
        else:
            print(resp)
            fp.write(resp)



if __name__ == "__main__":
    notify_url = "https://apihz.beecloud.cn/1/pay/webhook/receiver/9ce8115c-dc1f-4ab0-b776-ad9747e5ab4a"
    file_name = "D:\project\\auto_api_test\Result\\auto_api_log" + str(
        time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))) + ".txt"
    fp = open(file_name, 'w+')  # w+是新写  a+是续写
    tt = int(time.time()) * 1000
    host = gl.host
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    fp.write(now_time)
    fp.write('\n')
    app_id = gl.app_id
    app_secret = gl.app_secret
    isAgent=False
    # file_name = "E:\python learning\\api-test\Result\Result" + str(int(time.time())) + ".txt"
    # email = browser.find_element_by_id('email')
    # email.clear()
    # email.send_keys('436099562@qq.com')
    # browser.find_element_by_id("get_app_submit").click()

    for n in range(0,1):
        if n == 0:

            sign = sign_md5(app_id+str(tt)+app_secret)
            query_bill_para = {
                "app_id": app_id,
                "app_secret":app_secret,
                "app_sign": sign,
                "timestamp": tt,
                "return_url":"http://www.baidu.com"
            }
            if n == 0:
                # parentChannel_l = ['WX']
                parentChannel_l=['BC','ALI','WX']
            else:
                parentChannel_l = ['WX']
            # parentChannel_l = ['ALI']
            channel = {
                # 'BC':['BC_EXPRESS'],
                'BC': ['BC_WX_SCAN','BC_ALI_SCAN','BC_NATIVE','BC_ALI_QRCODE','BC_ALI_WAP','BC_ALI_APP','BC_EXPRESS'],
                'ALI': ['ALI_WEB', 'ALI_WAP', 'ALI_QRCODE', 'ALI_OFFLINE_QRCODE', 'ALI_SCAN'],
                'WX': ['WX_SCAN','WX_NATIVE'],
                'JD':['JD_WEB'],
                }
        for p_ch in parentChannel_l:

            for s_ch in channel[p_ch]:
                bill_no = str(uuid.uuid1()).replace('-', '')
                query_bill_para["bill_no"] = bill_no
                query_bill_para["channel"] = s_ch
                query_bill_para["notify_url"] = notify_url
                query_bill_para["optional"] = {'aa':'bb','aa1':'bb1'}
                query_bill_para["title"] = "BeeCloud 测试自动化"
                query_bill_para["total_fee"] = 1
                print("bill_no: "+bill_no)
                fp.write(bill_no + ":" + s_ch + '\n')

                if s_ch == "BC_WX_SCAN" or s_ch == "BC_ALI_SCAN" or s_ch == "ALI_SCAN" or s_ch == "WX_SCAN":
                    auth_code = input(s_ch + "'s auth_code:")
                    query_bill_para['auth_code'] = auth_code

                if isAgent == 'true':
                    url_temp = host + "/rest/offline/agent/bill"
                else:
                    if s_ch == 'BC_ALI_SCAN' or s_ch == 'BC_WX_SCAN' or s_ch == 'WX_SCAN' or s_ch == 'ALI_SCAN' or s_ch == 'ALI_OFFLINE_QRCODE':
                        url_temp = host + "/rest/offline/bill"
                    else:
                        url_temp = host + "/rest/bill"
                print(url_temp)
                print(query_bill_para)
                resp = request_post(url_temp, query_bill_para)
                if type(resp) == dict:
                    deal_with_pay(s_ch, resp, fp)
                    # webbrowser.open('pay_web.html', new=0)
                    # webbrowser.open('https://cli.im/api/qrcode/code?text='+resp['code_url'])
                else:
                    print(resp)
                time.sleep(1)

                if s_ch == "BC_WX_SCAN" or s_ch == "BC_ALI_SCAN" or s_ch == "ALI_SCAN" or s_ch == "WX_SCAN":
                    status_query_res = status_query(host, query_bill_para, s_ch, isAgent)
                    if status_query_res == 0:
                        continue

                query_bill_res = repeat_query_bill(fp, host, query_bill_para, s_ch)
                # bills成功之后在查询webhook
                if query_bill_res == 1:
                    # 微信支付是都查询webhook
                    if 'WX_SCAN' != s_ch:
                        repeat_query_webhook(fp, bill_no, s_ch)
                    else:
                        repeat_query_webhook(fp, bill_no, s_ch)
                else:
                    continue

    # print("transfer start:")
    # fp.write('-----  transfer start:\n')
    # transfer(fp, host)
    #
    # fp.write("fail channel:")
    # fp.write(str(gl.fail_channel))
    # fp.write("\n-------- End --------")
    fp.close()

# webbrowser.open('http://baidu.com')
# webbrowser.open('aaa.html',new=0)
# webbrowser.open('aaa.html',new=0)
# webbrowser.open('https://cli.im/api/qrcode/code?text=//cli.im')



