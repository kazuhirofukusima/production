class TimeTableData:
    '''
    引数としてバス時刻表データを受け取り，辞書型に変換し扱う
    '''

    def __init__(self, depPoint, depTime, arrPoint, arrTime, flag):
        '''
        コンストラクタ
        '''
        if '～' in depTime: # シャトル運行表示"～"に対応
            self.depTime = '～:～'
            self.arrTime = '～:～'
        else:
            self.depTime = depTime
            self.arrTime = arrTime

        self.depPoint = depPoint
        self.arrPoint = arrPoint
        self.shuttleFlag = flag



    def getData(self):
        '''
        バス時刻データを整形して返す
        '''
        if self.shuttleFlag: # シャトル運行時
            return '<現在シャトル運行> [{0}]{1} -> [{2}]{3}'.format(self.depPoint, self.depTime, self.arrPoint, self.arrTime)
        else:
            return '[{0}]{1} -> [{2}]{3}'.format(self.depPoint, self.depTime, self.arrPoint, self.arrTime)
