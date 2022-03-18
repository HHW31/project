from flask import Flask
app = Flask(__name__)

from flask import Flask, request, abort
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage

import requests
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

line_bot_api = LineBotApi('01IoZE40dlZHzUIMgKR/2BGflupgyn8We1cB4KSNEfUl6dH2QkyPasumxPmHLaNlEphl5M1WJf7NPCzrgJP4OeompSJVjgQqy2HBJsGmmua9MOBv46zXEF9U6MhSXwTAkoFj3ygMA2Wywrdw+h7C1AdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5b071bf676beb360cdeac26c2da060a2')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text
    if mtext == '@本期中獎號碼':
        try:
            #加入期別，呼叫mononum函式，取得本期中獎號碼。
            message = TextSendMessage(
                text=monoNum(0)
            )
            
            #使用line bot reply API回傳。
            line_bot_api.reply_message(event.reply_token,message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='讀取發票號碼發生錯誤！'))

    elif mtext == '@前期中獎號碼':
        try:
           #加入前期與前前期的期別，呼叫mononum函式，取得前期中獎號碼。
           #因為mononum函式回傳的是字串，所以可以使用「+=」的方式將兩期的中獎號碼結合在一起。
           #兩期中獎號碼中間可以加入一個空白列「\n\n」，較易閱讀。
            message = TextSendMessage(
                text =monoNum(1)+'\n\n'+ monoNum(2)              
            )
           #使用line bot reply API回傳。
            line_bot_api.reply_message(event.reply_token,message)            
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='讀取發票號碼發生錯誤！'))

    elif mtext == '@輸入發票最後三碼':
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入發票最後三碼進行對獎！'))
    
    # else if 判斷輸入的文字長度是3 以及 是數字
    # len(mtext) == 3 以及 mtext.isdigit()
    elif len(mtext) == 3 and mtext.isdigit():
        try:
            #取得xml
            content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
            #解析XML
            tree = ET.fromstring(content.text)
            #取得item標籤內容
            item = tree[0].find('item')
            #取處中獎號碼，並且存到變數ptext
            ptext = item[3].text
            ptext = ptext.replace('<p>','').replace('</p>','')  #將<p>用空白取代
            temlist = ptext.split('：')           #將ptext用「：」切割，並存入templist
            prizelist = []
            #特別獎或特獎後三碼
            prizelist.append(temlist[1][5:8])
            prizelist.append(temlist[2][5:8])
            #頭獎後三碼
            for i in range(3):
                prizelist.append(temlist[3][9*i+5:9*i+8])    
            #增開六獎
            sixlist = temlist[4].split('、')
            for i in range(len(sixlist)):
                prizelist.append(sixlist[i])
            #判斷是否中獎 
            
            if mtext in prizelist:
                message = TextSendMessage(
                    text='符合某獎項後三碼，請自行核對發票前五碼!\n\n'+monoNum(0)
                )
            else:
                message = TextSendMessage(
                    text='很可惜，未中獎。請輸入下一張發票最後三碼。'
                )
            #LINEBOT回覆message
            line_bot_api.reply_message(event.reply_token,message)
        except:
            #LINEBOT回覆「讀取發票號碼發生錯誤！」
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='讀取發票號碼發生錯誤！'))
    else:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入發票最後三碼進行對獎！'))

def monoNum(n):
    content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
    tree = ET.fromstring(content.text)  #解析XML
    items = list(tree.iter(tag='item'))  #取得item標籤內容
    title = items[n][0].text  #期別
    ptext = items[n][3].text  #中獎號碼
    #將中獎號碼字串中的<p>及</p>替換為「\n」換行符號
    ptext = ptext.replace('<p>','').replace('</p>','\n')
    return title + '\n' + ptext[:-1]  #ptext[:-1]為移除最後一個\n

if __name__ == '__main__':
    app.run()