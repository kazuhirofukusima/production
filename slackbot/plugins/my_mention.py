from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

import urllib.request, urllib.error #urlにアクセスするライブラリ
from bs4 import BeautifulSoup #parseHTMLとXMLのパーサー
import unicodedata # example -> unicodedata.normalize('NFKC', text) 全角から半角
import re # for Regular expression

from plugins import url # 適切なバス時刻表のURLを取得
from plugins import timeTableData # バス時刻表を取得し，指定の形式でデータを扱う

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
@respond_to('')
def main(message):
    messages = message.body['text'].split() # botに対する発言を取得
    topURL = 'http://www.teu.ac.jp/campus/access/006644.html' # 時刻表一覧が示されているページのURL

    # messagesからstatusとsendMessageを決定
    result = classify(messages)
    status = result['status'] # どのような処理を行うかの指標
    sendMessage = result['message'] # botの返答

    # statusにより処理を分ける
    if status=='help': # 説明
        sendMessage += getHelp()
    elif status=='list': # 使用可能な時刻表リスト
        sendMessage += getTimetableList(topURL)
    elif status=='time': # バス時刻検索
        sendMessage += getSearchResult(topURL, result['option'])
    else: # status==invalid(何らかの理由により無効)
        sendMessage += '使い方は \"へるぷ\" とメッセージを送って確認してね！'

    message.send(sendMessage)



'''
<function>
'''

def classify(messages):
    '''
    入力された値を判断，それに応じてresultを返す
    (result:[status:処理種類の指定, message:botの返答, (option:系統，検索の条件等をカンマ区切りで指定する)])
    '''
    result = {'status':None, 'message':None, 'option':None} # 戻り値, 辞書型

    # messegesから処理の種類・botの返答・系統や検索条件を指定し，resultに格納
    if len(messages)>=1 and len(messages)<=2: # 受け付け可能な単語数
        arg = messages[0]
        if re.search('ヘルプ|へるぷ|help', arg): # botの説明を表示
            result['status'] = 'help'
            result['message'] = '==busassi ヘルプ==\n\n'
        elif re.search('リスト|りすと|list', arg): # 利用可能な時刻表リストを表示
            result['status'] = 'list'
            result['message'] = '==現在利用できる時刻表リスト==\n\n'
            result['message'] += '\"[系統] [index]\"とメッセージを送ると，indexで指定した時刻表データで時刻検索を行うよ！\n\n'
        elif re.search('みなみ|はち|八|がく|学生', arg): # 必要なバス時刻を提示
            result['status'] = 'time'
            result['message'] = '==検索結果==\n\n'
            result['option'] = getOption(messages)
        else: # 受け付け不可な文字列
            result['status'] = 'invalid'
            result['message'] = '文字列｢{0}｣は無効だよ\n'.format(arg)
    else: # 受け付け不可な単語数
        result['status'] = 'invalid'
        result['message'] = '単語の数｢{0}｣は無効だよ\n'.format(len(messages))
    return result



def getOption(messages):
    '''
    messagesの内容を元に，result['option']に格納する「系統，検索の条件等を指定する文字列」を返す
    '''
    route = messages[0] # 系統(みなみ野 .etc)
    if re.search('みなみ', route): # みなみ野
        option = 'm'
    elif re.search('はち|八', route): # 八王子
        option = 'h'
    else: # 学生会館
        option = 'g'

    # 時刻表の指定がある場合(indexがある場合)
    if len(messages)==2:
        option += ',{0}'.format(messages[1])

    return option



def getHelp():
    '''
    このbotのヘルプを作成し返す
    '''
    helpMessage = '学バスbot busassi は，bot宛にメッセージを送ることで利用できるよ！\n'
    helpMessage += '基本的なメッセージと対応して行われる処理を以下に示すよ！\n\n'
    helpMessage += '------------------------\n'
    helpMessage += '\"へるぷ\"\n'
    helpMessage += 'botの説明を表示\n\n'
    helpMessage += '\"りすと\"\n'
    helpMessage += '利用できる時刻表リストを表示\n\n'
    helpMessage += '\"[系統]\"\n'
    helpMessage += 'バス時刻検索をする\n'
    helpMessage += '(系統:みなみ野，はちおうじ...)\n\n'
    helpMessage += '------------------------\n'
    helpMessage += '※ 同じ単語であれば，片仮名・漢字・英語の表現にも対応しているよ\n\n'
    helpMessage += '※ 単語間にはスペースを入力する必要があるよ\n\n'
    return helpMessage



def getTimetableList(topURL):
    '''
    topURLから利用可能な時刻表のURLを取得，整形したtimetableListを返す
    '''
    timetableList = '(例)\n[index]\ntimetable name\n'
    timetableList += '------------------------\n\n'

    list = url.getTarget(topURL, 'list')

    counter = 1
    for key in list:
        timetableList += '[{0}]\n{1}\n'.format(counter, key)
        counter += 1

    return timetableList + '\n\n※まだこの機能は使えないよ（常に基本時刻表が指定されるよ）'



def getSearchResult(topURL, option):
    '''
    必要なバス時刻を整形した文字列を返す
    '''
    option = unicodedata.normalize('NFKC', option).split(',') # 全角を半角にし，データを分割
    targetURL = getTargetURL(topURL, option) # 対象とする時刻表データのurlを取得

    if targetURL==None: # urlがない，つまり一般の日曜日など，運行自体がない場合
        return 'ごめんね，今日は運行がないよ...' + targetURL
    else: # 運行がある場合
        aptData, sendMessage = getAptData(targetURL, option[0]) # 指定の系統(option[0]:route)の全時刻データとメッセージを取得

    if aptData==None: # 学生会館へのバス運行がない場合
        return sendMessage + targetURL
    else:
        #busList = getBusList(aptData)
        return sendMessage + targetURL



def getTargetURL(topURL, option):
    '''
    ユーザが検索に使用する時刻表を指定しているか否かを判断し，適切な時刻表データのurlを返す
    '''
    if len(option)==2: # ユーザが使用する時刻表を指定した場合(現在未対応)
        return 'http://www.teu.ac.jp/campus/access/2018_kihon-a_bus.html'
    else: # 今日の時刻表のurlを取得
        return url.getTarget(topURL, 'url')



def getAptData(targetURL, route):
    '''
    指定された系統の時刻表データを全て取得，適切なメッセージとデータを返す
    '''
    try:
        # targetURLで指定したurlにアクセスし，内容を取得
        html= urllib.request.urlopen(targetURL)
        bsObj = BeautifulSoup(html, 'lxml')

        # bsObjから「tagName」で指定したタグ(時刻データ)のみ抽出
        tagName = 'tbody'
        allData = bsObj.findAll(tagName)

        # tbodyは系統の数だけあることを利用し，学生会館系統の運行がない場合を考慮
        if route=='g': # 学生会館をユーザが指定
            if len(allData)==3: # 学生会館への運行がある
                return allData[2], '系統：学生会館'
            else: # len(allData)==2 学生会館への運行がない
                return None, 'ごめんね，学生会館へのバスは運行がないよ...'
        else:
            if route=='m': # 系統:みなみ野
                return allData[0], '系統：みなみ野'
            else: # 系統:八王子
                return allData[1], '系統：八王子駅南口'
    except:
        import traceback
        traceback.print_exc()



def getBusList(aptData):
    '''
    キャンパスから駅(forStation)，駅からキャンパス(forCampus)への辞書型のバス時刻データリストを作成し返す
    '''
