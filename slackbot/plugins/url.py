import urllib.request, urllib.error #urlにアクセスするライブラリ
from bs4 import BeautifulSoup #parseHTMLとXMLのパーサー
import re # for Regular expression
import datetime # for year,month and day
import unicodedata # example -> unicodedata.normalize('NFKC', text) 全角から半角

from plugins import dateReplaceDict # 臨時時刻表の対応表



def getDate(dateStr): # dateStr:'today' or 'yyyy/mm/dd'
    '''
    日付と曜日を辞書型で返す
    '''
    if dateStr=='today':
        date = datetime.date.today()
    else:
        date = datetime.datetime.strptime(dateStr, '%Y/%m/%d')

    date = {
        'day':str(date.strftime('%Y%m%d')),
        'dayOfTheWeek':str(date.weekday())
    }
    return date


def replaceMulti(str, replaceDict):
    '''
    複数の文字列を置換する
    strをreplaceDictに照らし合わせて置換を行う
    '''
    for key, value in replaceDict.items():
        str = str.replace(key, value)
    return str


def optimizeKey(tag, replaceDict):
    '''
    今日の日付から参照すべき時刻表を判断すべく，keyを最適化する(kihon or yyyymmddのフォーマットに)
    '''
    key = replaceMulti(tag.attrs['href'], replaceDict)

    key = unicodedata.normalize('NFKC', key) # 全角数字や記号を半角に変換
    key = replaceMulti(key, dateReplaceDict.getDateDict()) # dateReplaceDictに応じてkeyの値を変換

    key = key.replace('_', '')
    return key


def getURL(urlDict):
    '''
    今日の日付と曜日(today)を元に適切な時刻表を返す
    '''
    # 日付と曜日を辞書型で取得
    date = getDate('today') # dateStr:'today' or 'yyyy/mm/dd'

    # targetURLの共通部分を指定
    targetURL = 'http://www.teu.ac.jp'

    if date['day'] in str(urlDict.keys()): # 今日の日付に該当する臨時時刻表があればそのURLを指定
        for key in urlDict.keys():
            if date['day'] in key:
                targetURL += urlDict[key]
                break
    elif date['dayOfTheWeek']=='6': # 今日が一般の日曜日なら運行がないので，Noneを指定
        targetURL = None
    elif date['dayOfTheWeek']=='5': # 今日が一般の土曜日なら基本時刻表（土曜日）のURLを指定
        targetURL += urlDict['saturday']
    else: # それ以外なら基本時刻表（平日）のURLを指定
        targetURL += urlDict['weekday']
    return targetURL




def getTarget(topURL, target): # target:'url' or 'list'
    '''
    topURLからtargetに応じたデータを返す(url:適切なURL, list:利用可能な時刻表のリスト)
    '''
    urlDict = {} # 時刻表のURLリスト（key:日付などURLの判別材料, value:URLそのもの）

    try:
        # topURLで指定されたページにあるバス時刻表へのリンク（aタグ & bus.htmlの文字列部分一致）を全て取得しtagsに格納
        html= urllib.request.urlopen(topURL)
        bsObj = BeautifulSoup(html, 'lxml')
        tags = bsObj.findAll(href=re.compile('bus.html'))
    except urllib.error.HTTPError:
        print('HTTPError')
    except:
        import traceback
        traceback.print_exc()
        print('Error')

    # tagsのaタグ内のhref(tags)から余分な文字列を削除
    replaceDict = dict.fromkeys(['/campus/access/', '_bus.html', 'bus.html'], '')
    for tag in tags:
        key = optimizeKey(tag, replaceDict) # kind of url, yyyymmdd
        if key not in 'delete':
            value = tag.attrs['href'] # url
            urlDict.setdefault(key, value)

    # targetに応じたデータを返す(url:適切なURL, list:利用可能な時刻表のリスト)
    if(target=='list'):
        return urlDict.keys()
    else:
        return getURL(urlDict)
