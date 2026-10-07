# APIにアクセスするためのクライアントを定義するモジュール
import requests
URL = "http://127.0.0.1:8080/"

def get_setting():
    # APIから初期設定データを取得する関数を定義する
    url = URL + "setting"
    response = requests.get(url, params={"token": "token-p3"})

    if response.status_code == 200:
        return response.json()
    else:
       return response.status_code


def get_day_data():
    url = URL
    # APIから日毎のデータを取得する関数を定義する
    response = requests.get(url, params={"token": "token-p3"})

    if response.status_code == 200:
        print("get_day_data response:", response.json())  # デバッグ用の出力
        return response.json()
    else:
       print("get_day_data failed with status code:", response.status_code)  # デバッグ用の出力
       return response.status_code


def post_agent_types(data):
    # APIにエージェントタイプを送信する関数を定義する
    url = URL + "agent"

    requests.post(
        url,
        params={"token": "token-p3"},
        json=data
    )

def post_agent_moves(data):
    # APIにエージェントの移動データを送信する関数を定義する
    url = URL

    return requests.post(
        url,
        params={"token": "token-p3"},
        json=data
    )
