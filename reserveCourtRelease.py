#!/usr/bin/env python
# coding: utf-8
# 流程说明：
# 1. 十二点前，获取Coookie，得到CookieString
# 2. 十二点前，获取场地信息courtJson，得到tomorrow，courtTimeIDMap，courtSubIDMap
# 3. 十二点前，生成场地表单formData，输入得到courtNum，courtTimeOne，courtTimeTwo
# 4. 十二点过几秒，通过CookieString，formData锁定场地资源，若成功，得到reserveID；若失败，输入新的Num和Time，重复3，4
# 5. 十二点过自定义时间，通过CookieString，tomorrow，courtNum，courtTimeOne，courtTimeTwo，reserveID提交预约表单
# 6. 哈哈哈哈哈哈哈哈哈哈哈哈还没大功告成

# 使用说明：
# 1. 将chromedriver.exe放到Python目录的Scripts文件夹下
# 2. 输入账号密码
# 3. 时间序列表示约场顺序，调整按照[]格式加入
# 4. 十二点之前运行

import datetime
import json
import time
import schedule
from datetime import date
from datetime import timedelta
from urllib import parse

import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# 浏览器设置
chromeOption = ChromeOptions()
chromeOption.add_experimental_option('excludeSwitches', ['enable-automation'])
chromeOption.add_experimental_option('useAutomationExtension', False)
chrome_options = Options()
chrome_options.add_argument("--headless")  # => 为Chrome配置无头模式
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
service = Service(r'C:\Python\Scripts\chromedriver.exe')
driver = webdriver.Chrome(service=service, options=chrome_options)


# 获取Cookie方法
def getCookie():
    # 打开登录界面
    loginURL = 'https://ca.csu.edu.cn/authserver/login?service=https%3A%2F%2Fehall.csu.edu.cn%2Fsite%2Flogin%2Fcas-login%3Fredirect_url%3Dhttps%253A%252F%252Fehall.csu.edu.cn%252Fv2%252Fsite%252Findex'
    driver.get(loginURL)

    # 模拟登录
    userName = ''  # 输入学号
    userPassword = ''  # 输入密码
    nameInput = driver.find_element(by=By.XPATH, value='//input[@id="username"]')
    passwordInput = driver.find_element(by=By.XPATH, value='//input[@id="password"]')
    loginButton = driver.find_element(by=By.XPATH, value='//a[@id="login_submit"]')
    nameInput.clear()
    passwordInput.clear()
    nameInput.send_keys(userName)
    passwordInput.send_keys(userPassword)
    loginButton.click()

    # 获取Cookie
    cookie = [item['name'] + '=' + item['value'] for item in driver.get_cookies()]
    cookieString = ''
    for value in cookie:
        cookieString += value + ';'
    print(cookieString)

    return cookieString


# 获取场地信息方法
def queryCourt(cookieString):
    tomorrow = (date.today() + timedelta(days=+1)).strftime("%Y-%m-%d")
    cookies = {'Cookie': cookieString}
    courtURL = 'https://ehall.csu.edu.cn/site/reservation/resource-info-margin?resource_id=25&start_time={0}&end_time={0}'.format(
        tomorrow)
    print(courtURL)
    while True:
        print('查询一次')
        response = requests.post(url=courtURL, cookies=cookies)
        nameNum = response.text.count("name")
        print(nameNum)
        if nameNum >= 2:
            break
        else:
            print('Waiting for Launch...')
            time.sleep(5)
    courtJson = response.json()['d']['218']

    courtNumMap = {}
    courtTimeMap = {}
    for courtInfo in courtJson:
        courtNumMap[courtInfo['abscissa']] = {}
        courtTimeMap[courtInfo['yaxis']] = {}
    courtTimeIDMap = {}
    courtSubIDMap = {}
    courtStatusMap = {}
    for num in courtNumMap:
        courtTimeIDMap[num] = {}
        courtSubIDMap[num] = {}
        courtStatusMap[num] = {}
        for courtTime in courtTimeMap:
            courtTimeIDMap[num][courtTime] = 0
            courtSubIDMap[num][courtTime] = 0
            courtStatusMap[num][courtTime] = 0
    for courtInfo in courtJson:
        courtTimeIDMap[courtInfo['abscissa']][courtInfo['yaxis']] = courtInfo['time_id']
        courtSubIDMap[courtInfo['abscissa']][courtInfo['yaxis']] = courtInfo['sub_id']
        courtStatusMap[courtInfo['abscissa']][courtInfo['yaxis']] = courtInfo['row']['status']

    return tomorrow, courtTimeIDMap, courtSubIDMap, courtStatusMap


# 生成可约的场地信息
# 5是行，4是不行，3是约满，1是可约
def generateAvailableCourtMap(courtStatusMap):
    availableCourtMap = {}
    for courtID, courtInfo in courtStatusMap.items():
        availableCourtMap[courtID] = []
        for courtTime, status in courtInfo.items():
            if status == 1:
                availableCourtMap[courtID].append(courtTime)
    print(availableCourtMap)
    return availableCourtMap


# 生成场地表单方法
def generateCourtForm(tomorrow, courtTimeIDMap, courtSubIDMap, availableCourtMap):
    formDataList = []
    courtDataList = []
    # 时间序列
    reserveTimeOrder = [
        ['21:00-21:30', '21:30-22:00'],
        ['19:00-19:30', '19:30-20:00'],
        ['19:30-20:00', '20:00-20:30'],
        ['20:30-21:00', '21:00-21:30'],
        ['20:00-20:30', '20:30-21:00'],
        ['10:00-10:30', '10:30-11:00']
    ]
    for period in reserveTimeOrder:
        for courtNum, courtTime in availableCourtMap.items():
            if period[0] in courtTime and period[1] in courtTime:
                # 资源表单
                courtDataOne = {
                    "date": "{}".format(tomorrow),
                    "period": courtTimeIDMap[courtNum][period[0]],
                    "sub_resource_id": courtSubIDMap[courtNum][period[0]]}  # 预约的场地信息
                courtDataTwo = {
                    "date": "{}".format(tomorrow),
                    "period": courtTimeIDMap[courtNum][period[1]],
                    "sub_resource_id": courtSubIDMap[courtNum][period[1]]}  # 预约的场地信息
                formData = {
                    "resource_id": "25",
                    "code": "",
                    "remarks": "",
                    "deduct_num": "",
                    "data": [courtDataOne, courtDataTwo]
                }
                formDataList.append(formData)
                courtDataList.append([courtNum, period[0], period[1]])
                print(formData)

    return formDataList, courtDataList


# 锁定场地资源方法
def lockCourt(cookieString, formDataList, courtDataList):
    tomorrow = (date.today() + timedelta(days=+1)).strftime("%Y-%m-%d")
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    cookies = {'Cookie': cookieString}
    lockURL = 'https://ehall.csu.edu.cn/site/reservation/launch'  # 锁定资源网址

    reserveID = 0
    courtInfo = ''

    # 两个场地预约
    for batch in range(10):
        print('循环锁定：第', batch, '次')
        for index in range(len(formDataList)):
            formData = formDataList[index]
            print(formData)
            data = parse.urlencode(formData)
            data = data.replace('+', '')
            data = data.replace('%27', '%22')
            response = requests.post(url=lockURL, headers=headers, cookies=cookies, data=data)
            responseDict = json.loads(response.text)
            print(responseDict)
            if responseDict['m'] == '操作成功':
                reserveID = responseDict['d']['appointment_id']
                courtData = courtDataList[index]
                courtInfo = "{0},${1}${2},{3}\n".format(courtData[0], tomorrow, courtData[1], courtData[2])
                break
        if reserveID != 0:
            break

    return reserveID, courtInfo


# 提交表单方法
def autoReserve(cookieString, reserveID, courtInfo):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    cookies = {'Cookie': cookieString}
    reserveURL = 'https://ehall.csu.edu.cn/site/apps/launch'
    applicantName = ""  # 申请人名字
    applicantNumber = ""  # 申请人学号
    applicantPhone = ""  # 申请人电话
    applicantCollege = ""  # 申请人学院
    memberNumber = ""  # 成员数
    courtInformation = courtInfo
    currentTime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    print(currentTime)
    reserveTime = currentTime
    memberInformationOne = {
        "UserSearch_25": {"uid": 391008, "name": "", "college": "", "number": ""},
        "Input_26": "", "Input_27": "", "Input_28": ""}
    memberInformationTwo = {
        "UserSearch_25": {"uid": 312138, "name": "", "college": "", "number": ""},
        "Input_26": "", "Input_27": "", "Input_28": ""}
    # 第零阶段预约表单
    zeroFormData = {
        "data": {"app_id": "454",
                 "node_id": "",
                 "form_data": {
                     "1582": {"Radio_4": {"value": "1", "name": "已阅读上述场地使用需知条例"},
                              "Radio_10": {"value": "1", "name": "负责人和使用人员已认真阅读并全面理解本书内容，且自愿签署责任书。"}}
                 },
                 "userview": 1
                 },
        "reserve_id": reserveID,
        "step": 0,
        "agent_uid": "",
        "starter_depart_id": 390555,
        "test_uid": 0
    }
    zeroData = parse.urlencode(zeroFormData)
    zeroData = zeroData.replace('+', '')
    zeroData = zeroData.replace('%27', '%22')
    zeroData = zeroData.replace('%24', '%20')
    # 第一阶段预约表单
    firstFormData = {
        "data": {"app_id": "454",
                 "node_id": "",
                 "form_data": {
                     "1572": {"User_4": applicantName, "User_6": applicantNumber, "User_8": applicantPhone,
                              "User_10": applicantCollege,
                              "User_54": "本科生", "Alert_39": "", "Alert_40": "", "Alert_41": "", "Alert_57": "",
                              "Input_12": memberNumber, "Input_14": courtInformation, "Input_30": "羽毛球馆（新校区）学生预约",
                              "Radio_37": {}, "Radio_49": {"name": ""}, "Radio_52": {"value": "1", "name": "学生个人预约"},
                              "Calendar_59": reserveTime, "Calendar_61": reserveTime,
                              "ShowHide_50": "", "ShowHide_55": "", "ShowHide_63": "",
                              "Validate_42": "", "Validate_43": "", "Validate_44": "", "Validate_45": "",
                              "Validate_47": "",
                              "Validate_64": "", "Validate_66": "",
                              "DataSource_34": "", "DataSource_38": "",
                              "RepeatTable_15": [memberInformationOne, memberInformationTwo]}
                 },
                 "userview": 1
                 },
        "reserve_id": reserveID,
        "step": 1,
        "agent_uid": "",
        "starter_depart_id": 390555,
        "test_uid": 0
    }
    firstData = parse.urlencode(firstFormData)
    firstData = firstData.replace('+', '')
    firstData = firstData.replace('%27', '%22')
    firstData = firstData.replace('%24', '%20')
    # 第二阶段预约表单
    secondFormData = {
        "data": {"app_id": "454",
                 "node_id": "",
                 "form_data": {
                     "1572": {"User_4": applicantName, "User_6": applicantNumber, "User_8": applicantPhone,
                              "User_10": applicantCollege,
                              "User_54": "本科生", "Alert_39": "", "Alert_40": "", "Alert_41": "", "Alert_57": "",
                              "Input_12": memberNumber, "Input_14": courtInformation, "Input_30": "羽毛球馆（新校区）学生预约",
                              "Radio_37": {}, "Radio_49": {"name": ""}, "Radio_52": {"value": "1", "name": "学生个人预约"},
                              "Calendar_59": reserveTime, "Calendar_61": reserveTime,
                              "ShowHide_50": "", "ShowHide_55": "", "ShowHide_63": "",
                              "Validate_42": "", "Validate_43": "", "Validate_44": "", "Validate_45": "",
                              "Validate_47": "",
                              "Validate_64": "", "Validate_66": "",
                              "DataSource_34": "", "DataSource_38": "",
                              "RepeatTable_15": [memberInformationOne, memberInformationTwo]}
                 },
                 "userview": 1,
                 "special_approver": [{"node_key": "UserTask_0e5zmo3", "uids": [391008], "subprocessIndex": ""}]
                 },
        "reserve_id": reserveID,
        "step": 1,
        "agent_uid": "",
        "starter_depart_id": 390555,
        "test_uid": 0
    }
    secondData = parse.urlencode(secondFormData)
    secondData = secondData.replace('+', '')
    secondData = secondData.replace('%27', '%22')
    secondData = secondData.replace('%24', '%20')

    # 发送请求
    zeroResponse = requests.post(url=reserveURL, data=zeroData, cookies=cookies, headers=headers)
    print(zeroResponse.text)
    zeroResponseDict = json.loads(zeroResponse.text)
    if zeroResponseDict['m'] == '操作成功':
        firstResponse = requests.post(url=reserveURL, data=firstData, cookies=cookies, headers=headers)
        print(firstResponse.text)
        firstResponseDict = json.loads(firstResponse.text)
        if firstResponseDict['m'] == '流程需要指定审批人':
            secondResponse = requests.post(url=reserveURL, data=secondData, cookies=cookies, headers=headers)
            print(secondResponse.text)


def doBeforeTwelve():
    cookieStringTemp = getCookie()
    tomorrowTemp, courtTimeIDMapTemp, courtSubIDMapTemp, courtStatusMapTemp = queryCourt(cookieStringTemp)
    availableCourtMapTemp = generateAvailableCourtMap(courtStatusMapTemp)
    formDataListTemp, courtDataListTemp = generateCourtForm(tomorrowTemp, courtTimeIDMapTemp, courtSubIDMapTemp,
                                                            availableCourtMapTemp)
    return cookieStringTemp, formDataListTemp, courtDataListTemp


def doAfterTwelve(cookieString, formDataList, courtDataList):
    cookieStringTemp = cookieString
    reserveIDTemp, courtInfoTemp = lockCourt(cookieString, formDataList, courtDataList)
    print(reserveIDTemp)
    print(courtInfoTemp)
    if reserveIDTemp != 0:
        autoReserve(cookieStringTemp, reserveIDTemp, courtInfoTemp)


def reserveCourt():
    one, two, three = doBeforeTwelve()
    doAfterTwelve(one, two, three)


if __name__ == '__main__':
    schedule.every().day.at("12:00").do(reserveCourt)
    while True:
        schedule.run_pending()
        print('Waiting...')
        time.sleep(8)
