from match_result import MatchResultReporter
import time
from gui.result_stats import replay_acquisitions
from typing import List
from api.api_client import get_setting, get_day_data, post_agent_types, post_agent_moves
from api.models2 import PreGameData, PreDateData, CellConverter
from divide_agent_type.car_divide import divide_initial_agents
from tour_car.compare_tourcar import calculate_tourcar
from tour_car.compute_astar import DIRECTIONS
from supply_car.compare_supplycar import calculate_supplycar
from PathSynchronizer import PathSynchronizer

class Setting_Pre_Game_Data():
    # ゲーム開始前の初期設定を取得し、データの格納やA*探索用セルデータへの変換を行うクラス

    def __init__(self):
        # APIからデータを取得する
        self.set_data = get_setting()

    def set_pre_game(self):
        # 初期設定データを受け取り、PreGameDataクラスのインスタンスを作成する
        self.pre_game = PreGameData(self.set_data)

    def Convert_map(self):
        # set_dataとPreGameDataのインスタンス(spotデータ)を使って、A*探索用のセルデータに変換する
        self.converted_map = CellConverter(
            self.pre_game.raw_map,
            self.pre_game.spots
        )


class DayData():
        # ゲーム開始後、日毎のデータを取得し、その度にデータの格納やA*探索用セルデータの更新を行うクラス

    def __init__(self):
        # APIからデータを取得する
        self.set_data = get_day_data()

    def set_pre_date(self):
        # 日毎のデータを受け取り、PreDateDataクラスのインスタンスを作成する
        self.pre_date = PreDateData(self.set_data)

    def Update_Convert_map(self, converted_map):
        # Converted_CellとPreDateDataのインスタンス(spotデータ)を使って、A*探索用のセルデータを更新する
        converted_map.rewrite_data(self.pre_date)


class Divide_AgentType():
    # エージェントの種類を分けるためのクラス

    def __init__(self, pre_game_data):
        # PreGameDataのインスタンスを受け取り、エージェントの種類を分ける
        self.pre_game_data = pre_game_data

    def Divide_agents(self):
        # PreGameDataのインスタンスからエージェントの種類を分ける
        self.divided_agents = divide_initial_agents(self.pre_game_data)

    def Json_output(self):
        # 分けたエージェントの種類をJSON形式で出力する
        # divided_agentsのkindsのみを返す

        return {
            "kinds": self.divided_agents["kinds"]
        }

    def Post_AgentType(self):
        # 分けたエージェントの種類をAPIに送信する
        post_agent_types(self.divided_agents["kinds"])


class Result_post():
    # 結果をPOSTするための処理をまとめるクラス

    def Json_output(self, daily_paths):
        # 結果データをJSON形式で出力する
        # 現在は仮のデータを返すが、実際にはフォーマットに従ったものを返すようにする
        moves = [[] for _ in daily_paths]

        # daily_pathsの各エージェントの経路を解析し、movesに変換する
        for agent in daily_paths:
            current_position = agent["start_position"]

            # 経路をフォーマットに従った形にし、movesに変換する
            for action in agent["path"]:

                if action["status"] == "wait":
                    moves[agent["agent_id"]].append(
                        -int(action["waiting_time"])
                    )
                    continue

                if action["status"] == "move":
                    next_position = action["position"]
                    # 移動方向をDIRECTIONSのインデックスに変換してmovesに追加する
                    direction = [
                        next_position[i] - current_position[i] for i in range(3)
                    ]

                    if direction == DIRECTIONS[0]:
                        moves[agent["agent_id"]].append(0)
                    elif direction == DIRECTIONS[1]:
                        moves[agent["agent_id"]].append(1)
                    elif direction == DIRECTIONS[2]:
                        moves[agent["agent_id"]].append(2)
                    elif direction == DIRECTIONS[3]:
                        moves[agent["agent_id"]].append(3)
                    elif direction == DIRECTIONS[4]:
                        moves[agent["agent_id"]].append(4)
                    elif direction == DIRECTIONS[5]:
                        moves[agent["agent_id"]].append(5)

                    current_position = next_position

            # 巡回車の余ったstepsを、movesに追加する
            if  agent["waiting_time"] > 0:
                moves[agent["agent_id"]].append(-(int(agent["waiting_time"])))

        return moves

    def Post_Result(self, moves):
        # 結果データをAPIに送信する
        return post_agent_moves(moves)
        

# 実行

# 1.1 初期設定の取得、PreGameDataの作成、A*探索用マップデータへの変換
setting = Setting_Pre_Game_Data()
setting.set_pre_game() #settingをselfとしてPreGameDataのインスタンスを作成する
setting.Convert_map()

# 1.2 エージェント毎の経路を格納するためのリストを作成する
daily_paths = []  # 各巡回車の経路を格納するリスト、日毎にリセットされる

# 2.エージェントタイプを決定、JSON形式で出力し、APIに送信する
divide = Divide_AgentType(setting.pre_game)
divide.Divide_agents()
post_data = divide.Json_output()
divide.Post_AgentType()

# 3. 開始時刻が確定し、試合が始まるまで待機
while True:
    data = get_setting()

    if not isinstance(data, dict):
        time.sleep(0.1)
        continue

    starts_at = data.get("startsAt", 0)

    if starts_at > 0:
        setting.pre_game.startsAt = starts_at

        if time.time() >= starts_at:
            break

    time.sleep(0.1)

# 5.1. PreGameDataのインスタンスをcalculate_tourcarに渡して初期化する
tourcar_calculator = calculate_tourcar(setting.pre_game)
supplycar_calculator = calculate_supplycar(setting.pre_game)

match_events = []
match_reporter = MatchResultReporter(setting.set_data, match_events)

# 4.試合終了まで日数分ループする
for day in range(len(setting.pre_game.daySteps)):
    # ゲーム開始後、日毎のデータを取得し、A*探索用セルデータの更新を行う
    day_data = DayData()
    day_data.set_pre_date()
    match_events.append(dict(day_data.set_data, type='day'))
    match_reporter.update()
    confirmed = replay_acquisitions(setting.set_data, {'events': match_events})
    if confirmed:
        tourcar_calculator.acquired_brands_match = set(confirmed['brands'])
    day_data.Update_Convert_map(setting.converted_map)
    daily_paths = [
        {
            "agent_id": agent_id,
            "agent_type": agent.kind,
            "start_position": list(setting.converted_map.cells[agent.pos].position),  # 最初の位置を格納する,
            "path": [],
            "waiting_time": 0
        } for agent_id, agent in enumerate(day_data.pre_date.agents)
    ]  # 各エージェントの経路を格納するリスト、日毎にリセットされる

    # 5.2 calculate_tourcarのインスタンスに日毎のデータを更新する
    tourcar_calculator.Update_Date(day_data.pre_date, setting.converted_map)
    supplycar_calculator.Update_Date(day_data.pre_date, setting.converted_map)

    while tourcar_calculator.has_remaining_tourcar_steps() or supplycar_calculator.has_remaining_supplycar_steps():

        before_tourcar_remaining_steps = sum(car["remaining_steps"] for car in tourcar_calculator.current_tourcars)
        before_supplycar_remaining_steps = sum(car["remaining_steps"] for car in supplycar_calculator.current_supplycars)

        # 5.3.1 経路探索を行う
        result_tourcar = tourcar_calculator.calculate_path_tourcar(pre_filter_count=5)
        supplycar_calculator.set_tour_context(
            tourcar_calculator.current_tourcars,
            tourcar_calculator.acquired_brands_today,
            tourcar_calculator.acquired_brands_match,
        )
        result_supplycar = supplycar_calculator.calculate_path_supplycar(
            result_tourcar["assignments"],
            tour_elapsed_steps={
                car["id"]: setting.pre_game.daySteps[day] - car["remaining_steps"]
                for car in tourcar_calculator.current_tourcars
            },
            choices_per_supply=5,
        )
        synchronizer = PathSynchronizer(
            result_tourcar["assignments"], result_supplycar["assignments"]
        )
        result_tourcar["assignments"], result_supplycar["assignments"] = (
            synchronizer.synchronize_paths(
                tourcar_calculator.current_tourcars,
                supplycar_calculator.current_supplycars,
                setting.converted_map,
                setting.pre_game.fuelLimits,
                setting.pre_game.daySteps[day],
            )
        )

        tourcar_calculator.record_synchronized_arrivals(result_tourcar['assignments'])

        # 同期済みの移動と途中待機を、そのまま回答に反映する。
        for assignment in result_tourcar["assignments"]:
            daily_paths[assignment["agent_id"]]["path"].extend(assignment["actions"])
        for assignment in result_supplycar["assignments"]:
            daily_paths[assignment["supply_id"]]["path"].extend(assignment["actions"])

        # 割り当てられたエージェントの情報を更新する
        tourcar_calculator.Update_current_tourcars(result_tourcar)  
        supplycar_calculator.Update_current_supplycars(result_supplycar)

        # エージェント達に変化がない場合はループを抜ける
        after_tourcar_remaining_steps = sum(car["remaining_steps"] for car in tourcar_calculator.current_tourcars)
        after_supplycar_remaining_steps = sum(car["remaining_steps"] for car in supplycar_calculator.current_supplycars)
        if (before_tourcar_remaining_steps == after_tourcar_remaining_steps and
            before_supplycar_remaining_steps == after_supplycar_remaining_steps):

            # 余ったstepを待機時間として保存する
            for car in tourcar_calculator.current_tourcars:
                if car["remaining_steps"] > 0:
                    daily_paths[car["id"]]["waiting_time"] += car["remaining_steps"]
                    car["remaining_steps"] = 0

            #余ったstepを待機時間として保存する(移動の時間に費やすように後々修正する)
            for car in supplycar_calculator.current_supplycars:
                if car["remaining_steps"] > 0:
                    daily_paths[car["id"]]["waiting_time"] += car["remaining_steps"]
                    car["remaining_steps"] = 0
            break

    # 5.4 結果をJSON形式で出力し、APIにPOSTする
    # 仮でresultをそのままPOSTするが、実際にはフォーマットに従ったものを返すようにする
    result_post = Result_post()
    moves = result_post.Json_output(daily_paths)
    response = result_post.Post_Result(moves)
    if response.status_code == 200:
        match_events.append({'type': 'post', 'endpoint': '/', 'day': day,
                             'payload': moves, 'body': response.text})
    match_reporter.update()


    # エージェントごとのパスをjson形式で出力し、APIにPOSTする

    # 当日の回答受付終了時間まで待機
    while time.time() < day_data.pre_date.endsAt:
        time.sleep(0.1)
match_reporter.update(completed=True)
