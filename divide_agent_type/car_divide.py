# エージェントタイプを分けるための関数をまとめたファイル
from api.models2 import CellConverter, PreDateData, PreGameData
from tour_car.compute_astar import AstarAlgorithm


def get_agents(data):
    # エージェントの情報だけ抜き取る
    # PreGameData / PreDateData または agents のリストからエージェントに関するリストを取り出す
    if isinstance(data, (PreGameData, PreDateData)):
        return data.agents

    return data


def count_agents(data): 
    # エージェントの数を数える
    agents = get_agents(data)
    return len(agents)


def divide_car_kinds(car_count): 
    # 0 or 1 に分ける
    # 0: 巡回車, 1: 補給車
    kind0_count = max(0, car_count - 1) # 補給車1台、残りは巡回車
    kind1_count = car_count - kind0_count # 残りのエージェントをkind1にする

    return [0] * kind0_count + [1] * kind1_count


def divide_initial_agents(data):
    agents = get_agents(data)
    car_count = len(agents)
    tourcar_count = max(0, car_count - 1)
    if not data.spots:
        # スポットがない場合は元のID順で割り当てる。
        return {"kinds": divide_car_kinds(car_count)}

    # 割り当てでは燃料の重みを外し、到着までの最小step数を比較する。
    # 開始前の道路は初期状態（渋滞なし）で評価する。
    astar = AstarAlgorithm(fuel_weight=0)
    astar.map_input(CellConverter(data.raw_map, data.spots))

    def nearest_spot_steps(agent_id):
        current_agent = {"position": agents[agent_id].pos, "fuel": float("inf")}
        best_steps = float("inf")
        for spot in data.spots:
            result = astar.search_astar(current_agent, spot.pos)
            if result["status"] == "reached_goal":
                best_steps = min(best_steps, result["path"][-1]["step"])
        return best_steps

    # 到達不能は後順位、同step数ならID順。kindsは元のエージェント順を保つ。
    ranked_ids = sorted(range(car_count),
                        key=lambda agent_id: (nearest_spot_steps(agent_id), agent_id))
    kinds = [1] * car_count
    for agent_id in ranked_ids[:tourcar_count]:
        kinds[agent_id] = 0
    return {"kinds": kinds}
