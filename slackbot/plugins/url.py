import urllib.request, urllib.error #urlにアクセスするライブラリ
from bs4 import BeautifulSoup #parseHTMLとXMLのパーサー
import re # for Regular expression
import datetime # for year,month and day
import unicodedata # example -> unicodedata.normalize('NFKC', text) 全角から半角

import dateReplaceDict # 臨時時刻表の対応表



def getToday():
    '''
    今日の日付と曜日を辞書型として返す
    '''
    today = {
        'date':str(datetime.date.today().strftime('%Y%m%d')),
        #'date':str(datetime.datetime(2018, 4, 13).strftime('%Y%m%d')),
        'dayOfTheWeek':str(datetime.date.today().weekday())
    }
    return today



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

    if 'kihon' in key: # 基本時刻表の場合(平日用と土曜日用)
        if 'b' in key: # 土曜日用の場合
            key = 'saturday'
        else: # 平日用の場合
            key = 'weekday'
    elif '-' in key: # 臨時時刻表で複数の日程が含まれている場合
        key = unicodedata.normalize('NFKC', key) # 全角数字や記号を半角に変換
        key = replaceMulti(key, dateReplaceDict.getDateDict())
    else: # 臨時時刻表で1日分のみの場合
        key = key.replace('-', '')

    key = key.replace('_', '')
    return key



def getURL(topURL):
    '''
    バス時刻表のURLの中から，今日の日付を用いて適切な時刻表を判断し，そのURLを返す
    '''
    target = None # 戻り値（適切な時刻表のURL）
    urlDict = {} # 時刻表のURLリスト（key:日付などURLの判別材料, value:URLそのもの）

    try:
        # topURLで指定されたページにあるバス時刻表へのリンク（aタグ & bus.htmlの文字列部分一致）を全て取得しtagsに格納
        html= urllib.request.urlopen(topURL)
        bsObj = BeautifulSoup(html, 'lxml')
        tags = bsObj.find_all(href=re.compile('bus.html'))
        targetURL = 'http://www.teu.ac.jp'
    except urllib.error.HTTPError:
        print('ページないよ！')
        return targetURL
    except:
        import traceback
        traceback.print_exc()
        return targetURL

    # 今日の日付を取得
    today = getToday()

    # aタグ内のhref(tags)から余分な文字列を削除する
    replaceDict = dict.fromkeys(['/campus/access/', '_bus.html', 'bus.html'], '')
    for tag in tags:
        key = optimizeKey(tag, replaceDict) # kind of url
        value = tag.attrs['href'] # url
        urlDict.setdefault(key, value)

    # 今日の日付(today['date'])を元に適切な時刻表を判断
    if today['date'] in str(urlDict.keys()): # 今日の日付に該当する臨時時刻表があればそのURLを指定
        for key in urlDict.keys():
            if today['date'] in key:
                targetURL += urlDict[key]
                break
    elif today['dayOfTheWeek']=='5': # 今日が土曜日なら基本時刻表（土曜日）のURLを指定
        targetURL += urlDict['saturday']
    else: # それ以外なら基本時刻表（平日）のURLを指定
        targetURL += urlDict['weekday']

    print('this case:{0}'.format(targetURL))
    return targetURL
