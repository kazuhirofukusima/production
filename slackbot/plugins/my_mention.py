from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

import urllib.request, urllib.error #urlにアクセスするライブラリ
from bs4 import BeautifulSoup #parseHTMLとXMLのパーサー

import re # for Regular expression

import datetime # for date

# @respond_to('string')     bot宛のメッセージ
#                           stringは正規表現が可能 「r'string'」
# @listen_to('string')      チャンネル内のbot宛以外の投稿
#                           @botname: では反応しないことに注意
#                           他の人へのメンションでは反応する
#                           正規表現可能
# @default_reply()          DEFAULT_REPLY と同じ働き
#                           正規表現を指定すると、他のデコーダにヒットせず、
#                           正規表現にマッチするときに反応
#                           ・・・なのだが、正規表現を指定するとエラーになる？

# message.reply('string')   @発言者名: string でメッセージを送信
# message.send('string')    string を送信
# message.react('icon_emoji')  発言者のメッセージにリアクション(スタンプ)する



'''
<main>
'''
@listen_to('バス')
@listen_to('ばす')
def main(message):

    url = 'http://www.teu.ac.jp/campus/access/2017_kihon-a_bus.html'
    searchWord = message.body['text'].split()

    try:
        html= urllib.request.urlopen(url)
        bsObj = BeautifulSoup(html, 'lxml')

        status = judge(searchWord, message)

        if status != 100:
            allData = assignData(status, bsObj)
            # 駅の時刻かキャンパスの時刻かを格納する
            startData = allData[::4]
            finishData = allData[1::4]

            resultData = getBusTime(startData, finishData)
            #message.send(str(resultData[0]))
            message.send(str(resultData[1]))

    except urllib.error.HTTPError:
        message.send('error:バス時刻表のページが見つからんよ！')
    except:
        import traceback
        traceback.print_exc()



'''
<<function>
'''


def judge(searchWord, message):
    '''
    入力された値を判断，それに応じてメッセージを送り，ステータスを返す
    '''
    if len(searchWord) == 2:
        busStop = searchWord[1]
        if re.search('みなみ', busStop):
            message.send('キャンパス → みなみ野駅だね！')
            return 0
        elif re.search('はち', busStop):
            message.send('キャンパス → 八王子駅だね！')
            return 1
        elif re.search('がくせい', busStop):
            message.send('がくせいかいかんだね！')
            return 2
        else:
            message.send('「'+ busStop + '」は知らないなあ〜')
            message.send('みなみの/はちおうじ .. から場所を指定してね！')
            return 100
    else:
        message.send('以下のように言ってくれると時刻に応じたバスの時刻を提示できるよ！')
        message.send('例）ばす [みなみの/はちおうじ/..]')
        return 100


def assignData(status, bsObj):
    '''
    バスデータを系統別に振り分ける
    '''
    tagName = 'tbody'
    minamino = bsObj.findAll(tagName)[0]
    hachioji = bsObj.findAll(tagName)[1]
    gakuseikaikan = bsObj.findAll(tagName)[2]

    return filterData(bsObj.findAll(tagName)[status])


def filterData(data):
    '''
    バスデータを指定された系統に絞りこむ
    '''
    tagName = 'td'
    data = data.findAll(tagName)

    for i in range(len(data)):
        data[i] = data[i].string # .stringで，タグ(data[i])内の文字列を取得

    return data


def getBusTime(startData, finishData):
    '''
    現在時刻を取得し，バスデータと比較・適切なバスデータを返す
    '''
    # {0:←0番目の引数（今回だとnow）が入る}
    now = datetime.datetime.now()
    nowHour = '{0:%H}'.format(now)
    nowMinute = '{0:%M}'.format(now)

    resultData = ['現在時刻 : ' + nowHour + ':' + nowMinute]

    # 指定時刻を元に適切なバスデータをgetApplyTime()により取得する
    busTimeData= getApplyTime(startData, finishData, nowHour, nowMinute)
    if busTimeData != 0:
        resultData.append(busTimeData)
        return resultData
    elif (int(nowHour)<22) and (int(nowHour)>5):
        nextHour = '{0:02d}'.format(int(nowHour)+1)
        nextMinute = '00'
        resultData.append(getApplyTime(startData, finishData, nextHour, nextMinute))
        return resultData
    elif int(nowHour)<6:
        nextHour = '07'
        nextMinute = '00'
        resultData.append(str(getApplyTime(startData, finishData, nextHour, nextMinute)) + '\n\n早いねー このバスは始発だよ!')
        return resultData
    else:
        resultData.append('ごめんね　今日の運行は終了したよ')
        return resultData


def getApplyTime(startData, finishData, hour, minute):
    '''
    バスデータの中からhourに該当し，かつminuteより時刻が遅いものがあればそのデータセットを返す
    '''
    for j in range(len(startData)):
        if (startData[j].startswith(hour)) and (startData[j].split(':')[1]>=minute):
            return '出発予定:' + startData[j] + ' → 到着予定: ' + finishData[j]
    return 0
