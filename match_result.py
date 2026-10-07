"""通常の main.py 実行でも、実サーバーの採択回答を保存・集計する。"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from gui.result_stats import replay_acquisitions


class MatchResultReporter:
    def __init__(self, source, events, directory=None):
        self.source = source
        self.events = events
        root = Path(directory or os.environ.get('HEXA_RESULT_DIR', 'results')).expanduser()
        self.directory = root / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
        self.directory.mkdir(parents=True, exist_ok=True)
        self.printed_days = set()
        print('試合結果の保存先:', self.directory.resolve(), flush=True)

    def update(self, completed=False):
        stats = replay_acquisitions(self.source, {'events': self.events, 'completed': completed})
        document = {'source': self.source, 'events': self.events,
                    'completed': completed, 'stats': stats,
                    'score_source': '採択回答と実サーバーの日次状態からの推計（公式スコアではありません）'}
        temporary = self.directory / 'match.json.tmp'
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.directory / 'match.json')
        if stats:
            for day in stats['days']:
                if day['types'] is not None and day['day'] not in self.printed_days:
                    print(format_day(day), flush=True)
                    self.printed_days.add(day['day'])
        if completed:
            print(format_summary(stats), flush=True)
        return stats


def format_day(day):
    return (f"{day['day'] + 1}日目: 獲得種類数 {day['types']} / 獲得数 {day['total_count']} "
            f"/ 未取得ブランド {day['missing_brands']}")


def format_summary(stats):
    if not stats:
        return '試合結果: 日次状態が取得できていないため集計できません'
    label = '試合結果（推計）' if stats['complete'] else '途中結果（集計済みの日のみ・推計）'
    lines = [label, f"合計獲得種類数: {stats['total_types']}",
             f"各日の獲得種類数の合計: {stats['cumulative_types']}",
             f"合計獲得数: {stats['total_count']}"]
    if stats['complete']:
        lines.extend([f"未取得ブランド: {stats['missing_brands']}",
                      f"全種類制覇: {not stats['missing_brands']}"])
    else:
        lines.append('全種類制覇・試合全体の未取得ブランド: 未集計の日があるため判定できません')
    lines.extend(stats['notes'])
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='保存済みの実サーバー試合結果を再表示')
    parser.add_argument('file', type=Path, help='results/<試合>/match.json')
    args = parser.parse_args()
    document = json.loads(args.file.expanduser().read_text(encoding='utf-8'))
    stats = replay_acquisitions(document['source'], document)
    if stats:
        for day in stats['days']:
            if day['types'] is not None:
                print(format_day(day))
            else:
                print(f"{day['day'] + 1}日目: 未集計")
    print(format_summary(stats))
