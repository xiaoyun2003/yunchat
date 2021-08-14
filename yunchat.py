#Import library
import sqlite3
import uuid
from urllib import parse
from socket import *
import os
import json
import time
import base64
from hashlib import md5
import re
import copy
import threading


ICON='''__    __  _   _   __   _   _____   _   _       ___   _____  
\ \  / / | | | | |  \ | | /  ___| | | | |     /   | |_   _| 
 \ \/ /  | | | | |   \| | | |     | |_| |    / /| |   | |   
  \  /   | | | | | |\   | | |     |  _  |   / / | |   | |   
  / /    | |_| | | | \  | | |___  | | | |  / /  | |   | |   
 /_/     \_____/ |_|  \_| \_____| |_| |_| /_/   |_|   |_| 1.0'''  
 
 
#base64
def b64(origStr):
    #base64 decode should meet the padding rules
    if(len(origStr)%3 == 1): 
        origStr += "=="
    elif(len(origStr)%3 == 2): 
        origStr += "=" 
    origStr = bytes(origStr, encoding='utf8')
    dStr = base64.b64decode(origStr).decode('utf-8','ignore')
    return dStr


 #1红色 2绿色 3黄色 4深蓝色 5紫色 6蓝色
def r(s,type):
    return input("\033[1;3"+str(type)+";m"+s+"\033[0m")   
def p(s,type):
    print("\033[1;3"+str(type)+";m"+s+"\033[0m")
#定义业务请求包
CPack={
 "types" :"unkonwn",
    "uid" : -1,
    "skey":"skey",
    "osinfo" :"from python_yunchat1.0",
    "data":{}}

#定义消息包
CMsg={
"types":"groups",
"subtypes":"subtypes",
"uid":-1,
"skey":"skey",
"msg":"msg",
"receiver":-1,
"sname":"sname"
}

#发包,业务包
def sendCPack(pack,port):
    sock=socket(AF_INET,SOCK_STREAM)
    sock.connect((Serve,port))
    sock.send(pack.encode())
    re=sock.recv(1024)
    sock.close()
    return re.decode()

#消息监听线程
class MsgL(threading.Thread):
    flag=0
    mid="0"
    def __init__(self,id,type):
        threading.Thread.__init__(self)
        self.id=id
        self.type=type
    def setFlag(self,flag):
        self.flag=flag
    def run(self):
        if self.type!="groups" and self.type!="friends":
            p("[Error]:错误的类型",1)
            exit()
        while True:
            mid=sql(1,"select MAX(mid) from msg",())[0]
            if mid=="" or mid==None:
                mid="0"
            if self.flag==-1:
                exit(0)
            gM=copy.deepcopy(CPack)
            gM["types"]="getmsg"
            gM["skey"]=Skey
            gM["uid"]=int(Uid)
            gM["data"]["mid"]=int(mid)
            sock=socket(AF_INET,SOCK_STREAM)
            sock.connect((Serve,Port2))
            sock.send(json.dumps(gM).encode())
            #设置阻塞，启动长轮询接受数据
            buffer=""
            while True:
                re=sock.recv(1024)
                if re:
                    buffer +=str(re.decode('utf-8','ignore'))
                else:
                    break
            #解析数据
            msj=json.loads(buffer)
            msgs=msj["Data"]["msg"]
            for i in msgs:
                
                #表名拿到的是当前主屏幕的数据
                if i["Receiver"]==int(self.id) and i["Types"]==self.type:
                    #发送数据给主屏幕
                    p("\n"+i["Sname"]+"(uid:"+str(i["Sender"])+")"+":"+b64(i["Msg"]),2)
                #写入数据到数据库
                if not sql(3,"select mid from msg where mid=?",(i["Mid"])):
                    insertMsg1(i)
                else:
                    sql(0,"update msg set type=?,mid=?,msgid=?,msg=?,sender=?,sname=?,receiver=? where mid="+str(i["Mid"]),(i["Types"],str(i["Mid"]),str(i["Msgid"]),i["Msg"],str(i["Sender"]),i["Sname"],str(i["Receiver"])))
        




#封装数据库操作
def sql(type,sql,t):
    re=""
    try:
        cx=sqlite3.connect(DBFile)
        cu=cx.cursor()
        if isinstance(t,int):
           pass
        else:
            if len(t)==0:
                cu.execute(sql)
            else:
                cu.execute(sql,t)
        cx.commit()
        if type==1:
            re=cu.fetchone()
        if type==2:
            re=cu.fetchall()
        if type==3:
            re=cu.fetchone()
            if re!=None:
                return True
            else:
                return False
        cu.close()
    except Exception as e:
        p("[ERROR]:"+str(e),1)
    return re

#检测元组数组中是否包含
def verTS(t,key,s):
    if t==None or len(t)==0:
        return False
    for i in t:
        if str(i[key])==s:
            return True
    return False
#基础命令
def baseCmd(cmd):
    if cmd=="/quit":
        p("拜拜|ε(*´･ω･)з",2)
        os._exit(0)
    if cmd=="/help":
        p("""
/login   登录账号
/register   注册账号
/help   查看帮助
/chatg gid   打开一个群组聊天
/chatf uid   打开一个好友聊天
/quit   退出本软件

tips:当打开一个群组或好友聊天之后输入信息，然后回车就会自动发送
        """,5)
    return False

#插入消息,
def insertMsg(data,type):
    sql(0,"insert into msg(type,mid,msgid,msg,sender,sname,receiver) values(?,?,?,?,?,?,?)",(type,data["mid"],data["msgid"],data["msg"],data["sender"],data["sname"],data["receiver"]))
#插入消息1
def insertMsg1(data):
    sql(0,"insert into msg(type,mid,msgid,msg,sender,sname,receiver) values(?,?,?,?,?,?,?)",(data["Types"],data["Mid"],data["Msgid"],data["Msg"],data["Sender"],data["Sname"],data["Receiver"]))

#显示消息
def displayMsg(d):
    data=d["Data"]
    
    p(data["sname"]+"(uid:"+str(data["sender"])+")"+":"+b64(data["msg"]),2)



#
def chatF(uid):
    res=sql(1,"select uname from friends where uid=?",(str(uid)))
    fn=res[0]
    p("当前好友:"+fn,3)
    #加载历史聊天记录，从本地
    msgs=sql(2,"select mid,msgid,msg,sender,sname from msg where type='friends' and receiver=? order by mid asc",(str(uid)))
    for msgr in msgs:
        p(msgr[4]+"(uid:"+str(msgr[3])+")"+":"+b64(msgr[2]),2)
  
    #启动一个线程监听
    th=MsgL(uid,"friends")
    th.start()
    global THl
    THl.append(th)
  
    msgP=copy.deepcopy(CMsg)
    #前端消息处理
    while True:
        msg=r(fn+"(uid:"+str(uid)+")>",4)
        if msg!="" and (not yunChatCmd(msg) and not baseCmd(msg)):
            msgP["msg"]=msg
            msgP["skey"]=Skey
            msgP["types"]="friends"
            msgP["subtypes"]="text"
            msgP["uid"]=int(Uid)
            msgP["sname"]=Uname
            msgP["receiver"]=int(uid)
            res=sendCPack(json.dumps(msgP),Port2)
            d=json.loads(res)
            if d["Code"]==200:
                #发送消息给主屏幕
                pass
            elif d["Code"]==102:
                p("[Error]:登录账号验证失效，请重新登录",1)
            else:
                p("[Error]:"+d["Data"]["tips"],1)

#
def chatG(gid):
    res=sql(1,"select gname from groups where gid=?",(str(gid)))
    gn=res[0]
    p("当前聊天室:"+gn,3)
    #加载历史聊天记录，从本地
    msgs=sql(2,"select mid,msgid,msg,sender,sname from msg where type='groups' and receiver=? order by mid asc",(str(gid)))
    for msgr in msgs:
        p(msgr[4]+"(uid:"+str(msgr[3])+")"+":"+b64(msgr[2]),2)
  
    #启动一个线程监听
    th=MsgL(gid,"groups")
    th.start()
    global THl
    THl.append(th)
  
    msgP=copy.deepcopy(CMsg)
    #前端消息处理
    while True:
        msg=r(gn+"(gid:"+str(gid)+")>",4)
        if msg!="" and (not yunChatCmd(msg) and not baseCmd(msg)):
            msgP["msg"]=msg
            msgP["skey"]=Skey
            msgP["types"]="groups"
            msgP["subtypes"]="text"
            msgP["uid"]=int(Uid)
            msgP["sname"]=Uname
            msgP["receiver"]=int(gid)
            res=sendCPack(json.dumps(msgP),Port2)
            d=json.loads(res)
            if d["Code"]==200:
                #发送消息给主屏幕
                pass
            elif d["Code"]==102:
                p("[Error]:登录账号验证失效，请重新登录",1)
            else:
                p("[Error]:"+d["Data"]["tips"],1)

#云聊基础命令
def yunChatCmd(cmd):
    if cmd=="/login":
       while True:
           ci=r("login>账号:",6)
           if ci=="":
               p("[Error]:账号不能留空",1)
               continue
           if not verStrE(ci):
               p("[Error]:账号只能纯英文",1)
               continue
           ci1=r("login>密码:",6)
           if ci1=="":
               p("[Error]:密码不能留空",1)
               continue
           #构造封包请求
           loginP=copy.deepcopy(CPack)
           loginP["types"]="login"
           loginP["data"]["user"]=ci
           loginP["data"]["pwd"]=pwd(ci+ci1)
           
           #调试
           print(loginP)
           
           #发送包
           jsonp=sendCPack(json.dumps(loginP),Port1)
           SPack=json.loads(jsonp)
           if SPack["Code"]==200:
               p("登录成功",2)
               global Skey
               global Uid
               global User
               global Uname
               Skey=SPack["Data"]["skey"]
               Uid=int(SPack["Uid"])
               Uname=SPack["Data"]["username"]
               User=SPack["Data"]["user"]
               if not sql(3,"select uid from user where uid=?",(str(Uid))):
                   sql(0,"insert into user(uid,uname,skey,user) values(?,?,?,?)",(str(Uid),Uname,Skey,User))
               else:
                   sql(0,"update user set uid=?,uname=?,skey=?,user=? where uid="+str(Uid),(str(Uid),Uname,Skey,User))
           else:
               p("[Error]:"+SPack["Data"]["tips"],1)
           return True
    if cmd=="/register":
        while True:
            ci=r("register>账号:",6)
            if ci=="":
                p("[Error]:账号不能留空",1)
                continue
            if not verStrE(ci):
                p("[Error]:账号只能纯英文",1)
                continue
            ci1=r("register>密码:",6)
            if ci1=="":
                p("[Error]:密码不能留空",1)
                continue
            ci2=r("register>确认密码:",6)
            if ci1!=ci2:
                p("[Error]:两次密码不一致",1)
                continue
            ci3=r("register>用户名:",6)
            if ci3=="":
                p("[Error]:用户名不能为空",1)
                continue
            loginP=copy.deepcopy(CPack)
            loginP["types"]="register"
            loginP["data"]["user"]=ci
            loginP["data"]["username"]=ci3
            loginP["data"]["pwd"]=pwd(ci+ci1)
            #构建封包
            jsonp=sendCPack(json.dumps(loginP),Port1)
            SPack=json.loads(jsonp)
            if SPack["Code"]==200:
                p("注册成功，现在可以愉快的登陆了呦",2)
                yunChatCmd("/login")
            else:
                p("[Error]:"+SPack["Data"]["tips"],1)
            return True
    global THl
    if cmd.find("/chatg")!=-1:
        for t in THl:
            t.setFlag(-1)
        s=cmd.split("/chatg",2)[1]
        chatG(int(s))
    if cmd.find("/chatf")!=-1:
        for t in THl:
            t.setFlag(-1)
        s=cmd.split("/chatf",2)[1]
        chatF(int(s))
    return False
#获取信息
def getUserInfo(type):
    P=copy.deepcopy(CPack)
    if type=="groups":
        P["types"]="getgroups"
    if type=="friends":
        P["types"]="getfriends"
    P["skey"]=Skey
    P["uid"]=int(Uid)
    j=sendCPack(json.dumps(P),Port1)
    S=json.loads(j)
    if S["Code"]==200:
        return S["Data"][type]
    if S["Code"]==102:
        print(S)
        print(P)
        return 102  
    else:
        p("[Error]:"+S["Data"]["tips"],1)
    return 0


#检测是否为合法
def verStrE(s):
    if parse.quote(s)!=s:
        return False
    else:
        return True
#pwd生成
def pwd(s):
    #异或
    sarr=bytearray(s,"utf-8")
    for i in range(len(sarr)):
        sarr[i]=(sarr[i]^5)|10
    m=md5()
    m.update(bytes(sarr))
    return m.hexdigest()



#程序入口
THl=[]
Skey=""
Uid=-1
Uname=""
User=""
#配置
DBFile="./yunchat.db"
Serve="123.57.56.248"
Port1=3521
Port2=3522

p(ICON,6)
p("Copyright © 2021 - 2021 xiaoyun. All Rights Reserved.小云 版权所有\n",1)

#初始化检测
if not os.path.exists(DBFile):
    cx=sqlite3.connect(DBFile)
    cu=cx.cursor()
    cu.execute("create table user(uid interge primary key unique, user text,uname text,skey text)")
    cu.execute("create table groups(gid interge primary key unique, gname text)")
    cu.execute("create table friends(uid interge primary key unique, uname text)")
    cu.execute("create table msg(mid integer primary key AUTOINCREMENT unique, msgid interger,msg text, type text, subtype text, sender integer, sname text, receiver interge, createtime timestamp);")
    cu.close()

#主菜单
#获取skey,如果没有就进入登录注册
res=sql(2,"select uid,user,uname,skey from user",())
if len(res)>1:
    p("*我们在您的系统中发现了多个账号，选择以下账号进行登陆*",4)
    for re in res:
        p("[uid:"+str(re[0])+"]"+str(re[2]),5)
    while True:
        ci=r("现在请输入uid来选择您的账号:",3)
        if verTS(res,0,ci):
            Skey=re[3]
            User=re[1]
            Uid=int(re[0])
            Uname=re[2]
            break
        if not baseCmd(ci):
            p("您输入的信息有误，请重新输入",1)
#
if len(res)==1:
    Skey=res[0][3]
    User=res[0][1]
    Uid=int(res[0][0])
    Uname=res[0][2]
if len(res)==0:
    while True:
        cmd=r("您还没有登录，现在您可以 登录/注册[/login /register]:",4)  
        if (not yunChatCmd(cmd)) and (not baseCmd(cmd)):
            p("指令有误，请重新输入",1)
        else:
            break


#into yunchat
p("正在加载中.....\n",2)
grs=getUserInfo("groups")
frs=getUserInfo("friends")
if grs==102 or frs==102:
    p("[Error]:当前账号身份验证失败，重新登陆",1)
if grs==0 or frs==0:
    pass



for i in grs:
    p("[*][gid:"+str(i["Gid"])+" "+str(i["Gname"]+"]"),5)
    if not sql(3,"select gid from groups where gid=?",(str(i["Gid"]))):
        sql(0,"insert into groups(gid,gname) values(?,?)",(str(i["Gid"]),str(i["Gname"])))
    else:
        sql(0,"update groups set gid=?,gname=? where gid="+str(i["Gid"]),(str(i["Gid"]),str(i["Gname"])))
for i in frs:
    p("[*][uid:"+str(i["Uid"])+" "+str(i["Uname"]+"]"),6)
    if not sql(3,"select uid from friends where uid=?",(str(i["Uid"]))):
        sql(0,"insert into friends(uid,uname) values(?,?)",(str(i["Uid"]),str(i["Uname"])))
    else:
        sql(0,"update friends set uid=?,uname=? where uid="+str(i["Uid"]),(str(i["Uid"]),str(i["Uname"])))



p("\n\n[∷tips:发送/help来查看使用和帮助∷]",2)


#主命令区
while True:
    cmd=r("yunchat>",6)
    baseCmd(cmd)
    yunChatCmd(cmd)
