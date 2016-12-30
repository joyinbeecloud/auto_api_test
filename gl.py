from entity import *
success = 0
fail = 0
all_process = 22#包括2个鉴权和3个打款，16个非服务商渠道，2个微信服务商,减去un的两个渠道,加上JD_WEB
host = url.url_dynamic
fail_channel=[]
app_id = beecloud_app.dateMove_app_id
app_secret = beecloud_app.dateMove_app_secret