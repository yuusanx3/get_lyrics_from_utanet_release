#---------------------------------------------------------------------------------------------------
# フォルダパスを指定して、指定したフォルダパスにある音楽ファイルの歌詞を更新します
# 歌ネットの歌詞を取得します
# 引数:フォルダパス
#---------------------------------------------------------------------------------------------------
# インストールパッケージ
# pip install beautifulsoup4
# pip install mutagen
#---------------------------------------------------------------------------------------------------
import wx
import threading
from get_lyrics_method import GetLyricsThread, GetLyrics

# メインフレームクラス
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None,  wx.ID_ANY, "歌詞取得アプリ", size=(400, 400))
        self.__create_widget()
        self.__do_layout()

    # Widgetを作成するメソッド
    def __create_widget(self):
        # テキスト
        self.text = wx.StaticText(self, label="フォルダパスを入力してください")
        # テキストボックス
        self.txtCtrl_folder = wx.TextCtrl(self, -1, size=(380, 20) )
        # ボタン
        self.button = wx.Button(self, label="決定")
        # ボタン押下時のイベント
        self.button.Bind(wx.EVT_BUTTON, self.OnButton)
        # プログレスバー
        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL, size=(380, 20))
        # テキストボックス(大きい)
        self.txtCtrl_log = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE, size=(380, 280))
        self.txtCtrl_log.SetEditable(False)

    # レイアウトを設定するメソッド
    def __do_layout(self):
        # レイアウトの設定
        sizer = wx.BoxSizer(wx.VERTICAL)
        # テキスト
        sizer.Add(self.text, flag=wx.ALIGN_LEFT)
        # テキストボックス
        sizer.Add(self.txtCtrl_folder, flag=wx.ALIGN_CENTER | wx.TOP, border=2)
        # ボタン
        sizer.Add(self.button, flag=wx.ALIGN_CENTER | wx.TOP, border=2)
        # プログレスバー
        sizer.Add(self.gauge, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        # テキストボックス(大きい)
        sizer.Add(self.txtCtrl_log, flag=wx.ALIGN_CENTER | wx.TOP, border=2)
        self.SetSizer(sizer) 

    # メッセージボックスを表示するメソッド
    def OnButton(self, event):
        if self.button.LabelText == "決定":
            # 処理呼び出し
            self.get_lyrics_thread = GetLyricsThread(self)
            self.get_lyrics_thread.start()
        else:
            self.get_lyrics_thread.kill()
        
# アプリケーションクラス
class App(wx.App):
    # wxPythonのアプリケーションクラスの初期化にはOnInitメソッドを使用する
    def OnInit(self):
        # フレームのオブジェクト生成
        frame = MainFrame()
        # 中央に配置
        frame.Centre()
        # メインフレームに設定
        self.SetTopWindow(frame)
        # フレームの表示
        frame.Show(True)
        return True

if __name__ == '__main__':
    # アプリケーションオブジェクトの生成
    app = App()
    # メインループ
    app.MainLoop()