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
import sys
import ctypes
import threading
import urllib.request
import requests
from bs4 import BeautifulSoup
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import USLT
import urllib.parse
import traceback
import logging
import re
import os

# URL
UTA_NET = "https://www.uta-net.com"
UTA_NET_SERCH_PAGE_1 = "/search/?Keyword="
UTA_NET_SERCH_PAGE_2 = "&Aselect=2&Bselect=3&pnum="
# フォルダパス
FOLDER_LOG = "./log/get_lyrics_from_folder_gui.log"

# ログの設定
if False == os.path.exists(os.path.dirname(FOLDER_LOG)):
    os.mkdir(os.path.dirname(FOLDER_LOG))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
loggerHandler = logging.FileHandler(FOLDER_LOG, encoding="UTF-8")
logger.addHandler(loggerHandler)
loggerFormat = logging.Formatter('%(asctime)s %(filename)s %(funcName)s [%(levelname)s]: %(message)s')
loggerHandler.setFormatter(loggerFormat)
# ログ個別設定
LOG_LYRICS = 0 # 0:歌詞をログに出力しない, 1:歌詞をログに出力する

class GetLyricsThread(threading.Thread):
    def __init__(self, wx_objct):
        super().__init__()
        self.wx_objct = wx_objct # wx.Frame

    def kill(self):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.native_id, ctypes.py_object(SystemExit))
        if ret > 1:
            # 状態が変更されたスレッドの数を返す。通常は、1。見つからなかった場合は、0。
            # たぶん必要ないが念のため。まだ送られていない例外を消去
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.native_id, None)  

    def run(self):
        GetLyrics(self.wx_objct)

class GetLyrics:
    def __init__(self, wx_objct):
        self.wx_objct = wx_objct # wx.Frame
        # テキストクリア
        self.wx_objct.txtCtrl_log.Clear()
        # ボタン無効化
        self.wx_objct.button.LabelText = "キャンセル"
        # フォルダパスのテキストボックスの値を読込
        target_folder_path = self.wx_objct.txtCtrl_folder.GetValue()
        # メイン処理
        self.main(target_folder_path)
        # プログレスバーを0にセット
        self.wx_objct.gauge.SetValue(0)
        # ボタン有効化
        self.wx_objct.button.LabelText = "決定"

    # メイン処理
    def main(self, target_folder_path):
        try:
            self.SetTxtCtrlLog("歌詞取得を開始します。")
            logger.info("----------歌詞取得を開始します----------")
            target_folder_path = target_folder_path.rstrip("\"").lstrip("\"")
            logger.info(f"フォルダパス:[{target_folder_path}]")

            success = 0 # 成功ファイル数
            target_cnt = 0 # 対象ファイル数
            target_cnt_pre = 0 # 対象ファイル数_事前計算
            lyrics_flg = 0 # 歌詞ありフラグ 0:無, 1:有

            for current_dir, sub_dirs, files_list in os.walk(target_folder_path):
                # 対象ファイル数_事前計算を計算
                target_cnt_pre += len(files_list)

            # フォルダパスのファイルリストを取得
            for current_dir, sub_dirs, files_list in os.walk(target_folder_path):
                wx.Yield()
                logger.info(f"現在のディレクトリ:[{current_dir}]")
                logger.info(f"総ファイル数:[{len(files_list)}]")

                # ファイルリストの繰り返し
                for file in files_list:

                    # タグから情報取得
                    if file.endswith(".mp3"):
                        tags = MP3(os.path.join(current_dir,file))
                        title = tags["TIT2"][0] # 曲名
                        artist = tags["TPE1"][0] # アーティスト
                    elif file.endswith(".m4a"):
                        tags = MP4(os.path.join(current_dir,file))
                        title = tags["©nam"][0] # 曲名
                        artist = tags["©ART"][0] # アーティスト
                    elif file.endswith(".flac"):
                        tags = FLAC(os.path.join(current_dir,file))
                        title = tags["title"][0] # 曲名
                        artist = tags["artist"][0] # アーティスト
                    else:
                        continue
                    target_cnt += 1

                    # 曲名を検索にヒットするように変更
                    title_serch_tmp = re.sub("\(.+?\)", "",  title)
                    title_serch_tmp = re.sub("\（.+?\）", "",  title_serch_tmp)
                    title_serch_tmp = re.sub("\[.+?\]", "",  title_serch_tmp)
                    title_serch_tmp = re.sub("\「.+?\」", "",  title_serch_tmp)
                    title_serch_tmp = re.sub("\-.+?\-", "",  title_serch_tmp)
                    nami = b'\xe3\x80\x9c'.decode("UTF-8")
                    title_serch_tmp = re.sub("\～.+?\～", "",  title_serch_tmp)
                    title_serch_tmp = re.sub("\~.+?\~", "",  title_serch_tmp)
                    title_serch_tmp = re.sub(f"\{nami}.+?\{nami}", " ", title_serch_tmp)
                    title_serch_tmp = title_serch_tmp.replace("("," ").replace(")"," ")
                    title_serch_tmp = title_serch_tmp.replace("（"," ").replace("）"," ")
                    title_serch_tmp = title_serch_tmp.replace("["," ").replace("]"," ")
                    title_serch_tmp = title_serch_tmp.replace("「"," ").replace("」"," ")
                    title_serch_tmp = title_serch_tmp.replace("～"," ").replace("~"," ").replace(f"{nami}"," ")
                    title_serch_tmp = title_serch_tmp.replace("！"," ").replace("!"," ")
                    title_serch_tmp = title_serch_tmp.replace("？"," ").replace("?"," ")
                    title_serch_tmp = re.sub("[…]", " ",  title_serch_tmp)
                    title_serch_list = title_serch_tmp.split(" ") # 検索用曲名リスト
                    # アーティスト名を検索にヒットするように変更
                    artist_serch_temp = re.sub("\(.+?\)", "",  artist)
                    artist_serch_temp = re.sub("\（.+?\）", "",  artist_serch_temp)
                    artist_serch_temp = re.sub("[ö]", "o",  artist_serch_temp)
                    artist_serch_temp = re.sub("[+]", " ",  artist_serch_temp)
                    artist_serch_list = re.split('[ ,]', artist_serch_temp)

                    self.SetTxtCtrlLog(f"処理中ファイル:[{target_cnt}/{target_cnt_pre}]")
                    self.SetTxtCtrlLog(f"アーティスト名:[{artist}], 曲名:[{title}]")
                    logger.info(f"ファイルパス:[{os.path.join(current_dir,file)}]")
                    logger.info(f"曲名:[{title}]")
                    logger.info(f"検索用曲名:[{title_serch_tmp}]")
                    logger.info(f"アーティスト名:[{artist}]")
                    logger.info(f"検索用アーティスト名:[{artist_serch_temp}]")
                    title_url_encoded = ""
                    for title_serch in title_serch_list:
                        logger.info(f"分割された検索用曲名:[{title_serch}]")
                        title_url_encoded += urllib.parse.quote(title_serch) + "+" # 曲名をURLエンコード
                    title_url_encoded = title_url_encoded.rstrip("+")
                    for artist_serch in artist_serch_list:
                        logger.info(f"分割されたアーティスト名:[{artist_serch}]")
                    lyrics_flg = False

                    # 曲名検索
                    # URLからHTML情報を取得 → 一致する曲名を検索
                    pnum = 1
                    while True:
                        logger.info("曲名検索URL:[{}]".format(UTA_NET + UTA_NET_SERCH_PAGE_1 + title_url_encoded + UTA_NET_SERCH_PAGE_2 + str(pnum)))
                        html_serch = requests.get(UTA_NET + UTA_NET_SERCH_PAGE_1 + title_url_encoded + UTA_NET_SERCH_PAGE_2 + str(pnum))
                        soup_serch = BeautifulSoup(html_serch.content, "html.parser")
                        soup_songlists = soup_serch.find_all("tbody",class_="songlist-table-body") # 曲名一覧table
                        for soup_songlist in soup_songlists:
                            soup_songs = soup_songlist.find_all("tr") # 曲名一覧tableのtrのリスト
                            # 曲名一覧tableのtrのリストの繰り返し
                            for soup_song in soup_songs:
                                song_serched = soup_song.find("span",class_="fw-bold songlist-title").text
                                artist_serched = soup_song.find("span",class_="d-block d-lg-none utaidashi").text
                                # 曲名、アーティストが一致しているか判定
                                song_match_flg = True # False:曲名、アーティストが一致していない, True:曲名、アーティストが一致している
                                if song_match_flg:
                                    for artist_serch in artist_serch_list:
                                        if not artist_serch in artist_serched:
                                            song_match_flg = False
                                            break # for artist_serch in artist_serch_list:
                                if song_match_flg:
                                    for title_serch in title_serch_list:
                                        if not title_serch in song_serched:
                                            song_match_flg = False
                                            break # for title_serch in title_serch_list:
                                # 曲名、アーティストが一致している場合
                                if song_match_flg:
                                    target_url = soup_song.find("a").get("href") # 歌詞ページのURL

                                    # 歌詞ページ検索
                                    # URLからHTML情報を取得 → 歌詞取得
                                    logger.info("歌詞ページURL:[{}]".format(UTA_NET + target_url))
                                    html_lyric = requests.get(UTA_NET + target_url)
                                    soup_lyric = BeautifulSoup(html_lyric.content, "html.parser")
                                    lyrics = soup_lyric.find("div",id="kashi_area") # 歌詞
                                    # 歌詞の改行コードの変更
                                    for lyric_row in lyrics.select("br"):
                                        lyric_row.replace_with('\r\n')

                                    # タグ更新
                                    if file.endswith(".mp3"):
                                        tags[u"USLT::'eng'"] = USLT(encoding=3, lang=u"eng", desc=u"desc", text=lyrics.text)
                                    elif file.endswith(".m4a"):
                                        tags["©lyr"] = lyrics.text
                                    elif file.endswith(".flac"):
                                        tags["lyrics"] = lyrics.text
                                    tags.save()
                                    if 1 == LOG_LYRICS:
                                        logger.info("▼歌詞")
                                        logger.info(lyrics.text)
                                        logger.info("▲")
                                    success += 1
                                    lyrics_flg = True
                                    break # for soup_song in soup_songs:

                            if lyrics_flg == True:
                                break # for soup_songlist in soup_songlists:
                        
                        if 0 != len(soup_songlists) and lyrics_flg == False:
                            pnum += 1
                        else:
                            break # while True:
                        
                    if lyrics_flg == True:
                        self.SetTxtCtrlLog(">>歌詞あり")
                        logger.info(">>歌詞あり")
                    else:
                        self.SetTxtCtrlLog(">>歌詞なし")
                        logger.info(">>歌詞なし")
                    
                    # プログレスバーセット
                    self.SetGauge( int( target_cnt/target_cnt_pre*100 ))

            self.SetTxtCtrlLog("検索ファイル数:[{}], 歌詞ありファイル数:[{}]".format(target_cnt, success))
            logger.info("検索ファイル数:[{}], 歌詞ありファイル数:[{}]".format(target_cnt, success))
        except SystemExit:
            self.SetTxtCtrlLog("キャンセルしました。")
            logger.info("キャンセルしました。")
        except:
            self.SetTxtCtrlLog("予期しないエラーが発生しました。")
            logger.info("予期しないエラーが発生しました。")
            logger.info(traceback.format_exc())

        finally:
            self.SetTxtCtrlLog("歌詞取得を終了します。")
            logger.info("----------歌詞取得を終了します----------")

    # プログレスバーの設定
    def SetGauge(self, value):
        self.wx_objct.gauge.SetValue(value)

    # ログメッセージの設定
    def SetTxtCtrlLog(self, text):
        self.wx_objct.txtCtrl_log.AppendText(text +"\n")