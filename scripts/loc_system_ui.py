#!/usr/bin/env python3
"""In-place Chinese loc for Utage system UI (no textures).

- sharedassets1 TextAssets 67-70: replace Japanese TSV column
- level1 / sa1 Ugui m_Text (last field): replace if it fits
Skip: book, layers pid 202, punctuation 208, ボタンN, Effekseer, textures.
"""
import os, shutil, struct, sys
import UnityPy

SA1 = "/tmp/noesis/hd/NOeSIS HD_Data/sharedassets1.assets"
L1 = "/tmp/noesis/hd/NOeSIS HD_Data/level1"
BAK_DIR = "/tmp/noesis/backup"
BAK_SA1 = os.path.join(BAK_DIR, "sharedassets1.assets.pre-ui")
BAK_L1 = os.path.join(BAK_DIR, "level1.pre-ui")

# Exact JP -> CN. Keys/English columns stay. Keep {0} {1} {2} and newlines.
MAP = {
    # SystemText / ExampleText / common buttons
    "はい": "是",
    "いいえ": "否",
    "キャンセル": "取消",
    "もどる": "返回",
    "戻る": "返回",
    "クリア": "清除",
    "リトライ": "重试",
    "履歴": "历史",
    "セーブ": "保存",
    "ロード": "读取",
    "オン": "开",
    "オフ": "关",
    "スキップ": "跳过",
    "なし": "无",
    "サウンド": "声音",
    "レビュー": "回顾",
    "リストア": "还原",
    "ダウンロード": "下载",
    "ゲームを終了しますか？": "要退出游戏吗？",
    "●デバッグ情報": "●调试信息",
    "●デバッグログ": "●调试日志",
    "●デバッグメニュー": "●调试菜单",
    "デバッグ情報": "调试信息",
    "セーブ消去＆終了": "清除存档并退出",
    "ｷｬｯｼｭﾌｧｲﾙ削除": "删除缓存",
    "言語": "语言",
    "「宴」のセーブデータを消去": "清除「宴」的存档",
    "「宴」のセーブデータを全て消去しますか？": "要清除「宴」的全部存档吗？",
    "「宴」のキャッシュファイルを消去": "清除「宴」的缓存文件",
    "「宴」のキャッシュファイルを全て消去しますか？": "要清除「宴」的全部缓存吗？",
    "「宴」の出力ファイルを消去": "清除「宴」的输出文件",
    "「宴」の出力ファイル（セーブデータとキャッシュファイル）を全て消去しますか？": "要清除「宴」的全部输出文件（存档和缓存）吗？",
    "ダウンロード中です...": "正在下载...",
    "ダウンロード完了！": "下载完成！",
    "ネットワークにつながっていません": "未连接到网络",
    "サイズの大きいデータがダウンロードされます。Wifi接続ではないですがよろしいですか。": "将下载较大数据。当前不是 Wi-Fi，是否继续？",
    "現在のシナリオプロジェクトファイルを変更します": "将更改当前剧本工程文件",
    "宴のシーンをバージョンアップする必要があります。よろしいですか": "需要升级宴的场景。可以吗？",
    "宴のシナリオを再インポートしてバージョンアップする必要があります。よろしいですか": "需要重新导入宴的剧本并升级。可以吗？",
    "再ﾀﾞｳﾝﾛｰﾄﾞ": "重新下载",
    "はじめから": "从头开始",
    "コンフィグ": "设置",
    "タイトル": "标题",
    "ﾃﾞﾌｫﾙﾄ\nに戻す": "恢复\n默认",
    "ﾃﾞﾌｫﾙﾄ\\nに戻す": "恢复\\n默认",
    "メッセージ速度": "文字速度",
    "自動メッセージ速度": "自动播放速度",
    "ウインドウの透明度": "窗口透明度",
    "未読でもスキップする": "跳过未读文本",
    "選択肢でスキップ解除": "选项处解除跳过",
    "マウスホイールで\n文字送り": "滚轮\n推进文字",
    "マウスホイールで\\n文字送り": "滚轮\\n推进文字",
    "フルスクリーン表示": "全屏显示",
    "音量": "音量",
    "全体": "全部",
    "環境音": "环境音",
    "ボイス": "语音",
    "次の音声まで再生を続ける": "播放至下一句语音",
    "クリックで停止": "点击停止",
    "CG回想": "CG回想",
    "シーン回想": "场景回想",
    "サウンドルーム": "音乐室",
    "ギャラリー": "鉴赏",
    "カテゴリ名": "分类名",
    "セーブファイル\nテキスト": "存档文件\n文本",
    "シーン回想\nテキスト": "场景回想\n文本",
    "ゲームデータをロード中です": "正在读取游戏数据",
    "タイトルへ戻る": "返回标题",
    # AdvErrorMsg
    "インポート {0}": "导入 {0}",
    "{0}: はリンク先が存在しないシナリオラベルです\n{1}": "{0}: 链接目标不存在的剧本标签\n{1}",
    "{0}: はリンク先が存在しないシナリオラベルです\\n{1}": "{0}: 链接目标不存在的剧本标签\\n{1}",
    "{0}: 二重に定義されたシナリオラベルです\n{1}": "{0}: 重复定义的剧本标签\n{1}",
    "{0}: 二重に定義されたシナリオラベルです\\n{1}": "{0}: 重复定义的剧本标签\\n{1}",
    "{0}: はジャンプ先が存在しないシナリオラベルです": "{0}: 跳转目标不存在的剧本标签",
    "{0}: はSetting用のシートではありません": "{0}: 不是 Setting 用的表",
    "{0}: 不明なタグです": "{0}: 未知标签",
    "サウンド{0}のタイプは{1}ですが、{2}として使用しようしました": "声音{0}的类型是{1}，却要当作{2}使用",
    "Bg用のLayerが設定されていません。": "未设置背景用图层。",
    "セーブデータの読み込みに失敗しました。レイヤー[{0}]が設定されていません": "读取存档失败。未设置图层[{0}]",
    "{0}: ifがないままElseIfが始まっています": "{0}: 没有 if 就开始了 ElseIf",
    "ifがないままElseが始まっています": "没有 if 就开始了 Else",
    "ifがないままEndifが始まっています": "没有 if 就开始了 Endif",
    "不正な記述です": "写法无效",
    "{0}:はシナリオラベルではありません": "{0}: 不是剧本标签",
    "{0}: という名前のGameObjectcが見つからなかったためTween処理が出来ませんでした。": "找不到名为 {0} 的 GameObject，无法做 Tween。",
    "シーン{0}が終わっていなのに、新しいシーン{1}に移っているいます。別のシナリオに移る前にEndSceneGalleryを使ってください。": "场景{0}尚未结束就进入了新场景{1}。请先使用 EndSceneGallery。",
    "シーン回想に登録されていないのに、シーン回想終了がされています。": "未登记场景回想却调用了结束回想。",
    "文字数={0}": "字数={0}",
    # ErrorMsg (keep trailing spaces)
    "{0}:が見つかりません": "{0}: 找不到",
    " {0}: は不明なタイプです": " {0}: 是未知类型",
    "{0}は不明なバージョンです": "{0}是未知版本",
    "カラー:{0} は書式が間違っています": "颜色:{0} 格式错误",
    "{0} ミップマップのあるテクスチャをスプライトに設定しようとしています": "{0} 正把带 mipmap 的贴图设为精灵",
    "フォントに未設定の文字です。 [ {0} ]": "字体中未包含该字符。 [ {0} ]",
    "列:{0} は存在しないかデータが空です。": "列:{0} 不存在或数据为空。",
    "{0} 列目は存在しないかデータが空です。": "第 {0} 列不存在或数据为空。",
    "{0}  列目のデータ: {1} を値に変換できません。正しい書式で入力してください": "第 {0} 列的数据: {1} 无法转换。请按正确格式输入",
    "{0}:ヘッダーに指定した行が存在しません\n{1}": "{0}: 表头指定的行不存在\n{1}",
    "{0}:ヘッダーに指定した行が存在しません\\n{1}": "{0}: 表头指定的行不存在\\n{1}",
    "{0}:指定の名前の列は見つかりません\n\\{1}": "{0}: 找不到指定名称的列\n\\{1}",
    "{0}:指定の名前の列は見つかりません\\n\\{1}": "{0}: 找不到指定名称的列\\n\\{1}",
    "{0}:はまだ再生準備が終わってません": "{0}: 尚未完成播放准备",
    "セーブすべきでないTween情報をセーブしようとしました": "试图保存不应保存的 Tween 信息",
    "{0} ファイル書き込みエラー {1}": "{0} 文件写入错误 {1}",
    "{0} ファイル読み込みエラー {1}": "{0} 文件读取错误 {1}",
    "メモリリーク": "内存泄漏",
    "ファイルを参照しているオブジェクトがNULLです": "引用该文件的对象为 NULL",
    "ファイルの使用準備が終わっていません。「ReadyToUse」を使ってください": "文件尚未准备好。请使用「ReadyToUse」",
    "ロード済みのファイルのロードフラグは変えられません": "不能更改已加载文件的加载标志",
    "ロード済みのファイルのバージョンは変えられません": "不能更改已加载文件的版本",
    "シングルトンなオブジェクトを二個以上作ろうとしました": "试图创建两个以上的单例对象",
    "キャッシュ書き込みしないファイルです": "这是不写入缓存的文件",
    "{0} :不明なパラメーターです。": "{0} :未知参数。",
    "式の結果がbool型ではありません": "表达式结果不是 bool",
    "不正な式の記述です": "表达式写法无效",
    "ピボット:{0} は書式が間違っています": "轴心:{0} 格式错误",
    "テキストに不正な書式があります。< {0}": "文本格式无效。< {0}",
    "文字列を数式に変換するコールバックが登録されていません ": "未注册把字符串转成算式的回调 ",
    "演算に失敗しました ": "运算失败 ",
    "{0} に {1} を代入できません ": "无法将 {1} 赋给 {0} ",
    "演算子:{0} を適用できません ": "无法应用运算符:{0} ",
}

SKIP_EXACT = {
    "ボタン1", "ボタン2", "ボタン3",
    "OK", "BGM", "SE", "{0}/{1}",
}


def span_for(n):
    pad = (4 - (n % 4)) % 4
    return 4 + n + pad


def patch_last_string(raw, new_s):
    """Replace the last Unity string in an object blob if it fits."""
    i = 0
    last = None
    n = len(raw)
    while i + 4 <= n:
        ln = int.from_bytes(raw[i:i + 4], "little", signed=True)
        if 0 <= ln <= n - i - 4:
            chunk = raw[i + 4:i + 4 + ln]
            try:
                chunk.decode("utf-8")
            except Exception:
                i += 1
                continue
            if b"\x00" in chunk:
                i += 1
                continue
            pad = (4 - (ln % 4)) % 4
            last = (i, ln, pad)
            i += 4 + ln + pad
            continue
        i += 1
    if last is None:
        return raw, "no-string", None
    off, ln, pad = last
    old = raw[off + 4:off + 4 + ln].decode("utf-8")
    nb = new_s.encode("utf-8")
    need = span_for(len(nb))
    room = n - off
    if need > room:
        return raw, "no-fit", old
    out = bytearray(raw)
    out[off:off + 4] = struct.pack("<i", len(nb))
    out[off + 4:off + 4 + len(nb)] = nb
    # zero the rest of the object so we do not leave stale JP bytes
    for j in range(off + 4 + len(nb), n):
        out[j] = 0
    return bytes(out), "ok", old


def loc_tsv(text):
    lines = text.splitlines(keepends=True)
    out = []
    miss = []
    changed = 0
    for line in lines:
        nl = ""
        body = line
        if body.endswith("\r\n"):
            nl, body = "\r\n", body[:-2]
        elif body.endswith("\n"):
            nl, body = "\n", body[:-1]
        if not body.strip() or body.startswith("Key\t"):
            out.append(body + nl)
            continue
        parts = body.split("\t")
        if len(parts) < 3:
            out.append(body + nl)
            continue
        jp = parts[1]
        if jp in SKIP_EXACT or jp == "Japanese":
            out.append(body + nl)
            continue
        if jp in MAP:
            parts[1] = MAP[jp]
            changed += 1
        else:
            # already Chinese or leftover
            if any("\u3040" <= c <= "\u30ff" for c in jp) or any(
                "\uff66" <= c <= "\uff9d" for c in jp
            ):
                miss.append(jp)
        out.append("\t".join(parts) + nl)
    return "".join(out), changed, miss


def backup():
    os.makedirs(BAK_DIR, exist_ok=True)
    if not os.path.exists(BAK_SA1):
        shutil.copy2(SA1, BAK_SA1)
        print("backup sa1 ->", BAK_SA1)
    else:
        print("sa1 pre-ui backup exists")
    if not os.path.exists(BAK_L1):
        shutil.copy2(L1, BAK_L1)
        print("backup l1 ->", BAK_L1)
    else:
        print("l1 pre-ui backup exists")


def patch_textassets(path, pids):
    data = bytearray(open(path, "rb").read())
    env = UnityPy.Environment()
    f = env.load_file(path)
    stats = []
    for pid in pids:
        o = f.objects[pid]
        raw = o.get_raw_data()
        # name then script
        nlen = int.from_bytes(raw[0:4], "little", signed=True)
        npad = (4 - (nlen % 4)) % 4
        soff = 4 + nlen + npad
        slen = int.from_bytes(raw[soff:soff + 4], "little", signed=True)
        script = raw[soff + 4:soff + 4 + slen].decode("utf-8")
        new_script, changed, miss = loc_tsv(script)
        nb = new_script.encode("utf-8")
        room = o.byte_size - soff
        need = span_for(len(nb))
        name = raw[4:4 + nlen].decode("utf-8")
        if need > room:
            stats.append((name, "NOFIT", len(nb), room, changed, miss))
            continue
        new_raw = bytearray(raw)
        new_raw[soff:soff + 4] = struct.pack("<i", len(nb))
        # grow/shrink within object
        filled = bytearray(o.byte_size)
        filled[:soff] = raw[:soff]
        filled[soff:soff + 4] = struct.pack("<i", len(nb))
        filled[soff + 4:soff + 4 + len(nb)] = nb
        data[o.byte_start:o.byte_start + o.byte_size] = filled
        stats.append((name, "ok", len(nb), room - 4, changed, miss))
    open(path, "wb").write(data)
    return stats


def patch_ugui(path, skip_pids=None):
    skip_pids = skip_pids or set()
    data = bytearray(open(path, "rb").read())
    env = UnityPy.Environment()
    f = env.load_file(path)
    rows = []
    for o in f.objects.values():
        if o.class_id != 114 or o.byte_size > 400 or o.path_id in skip_pids:
            continue
        raw = o.get_raw_data()
        if len(raw) < 132:
            continue
        ln = int.from_bytes(raw[128:132], "little", signed=True)
        if not (1 <= ln <= 80) or 132 + ln > len(raw):
            continue
        try:
            s = raw[132:132 + ln].decode("utf-8")
        except Exception:
            continue
        if s in SKIP_EXACT:
            rows.append((o.path_id, "skip", s, s))
            continue
        if s not in MAP:
            # leftover kana?
            if any("\u3040" <= c <= "\u30ff" for c in s) or any(
                "\uff66" <= c <= "\uff9d" for c in s
            ):
                rows.append((o.path_id, "miss", s, s))
            continue
        new_s = MAP[s]
        new_raw, st, old = patch_last_string(raw, new_s)
        if st != "ok":
            rows.append((o.path_id, st, s, new_s))
            continue
        data[o.byte_start:o.byte_start + o.byte_size] = new_raw
        rows.append((o.path_id, "ok", s, new_s))
    open(path, "wb").write(data)
    return rows


def main():
    backup()
    print("=== TextAssets ===")
    for name, st, nlen, room, changed, miss in patch_textassets(SA1, (67, 68, 69, 70)):
        print(f"  {name}: {st} utf8={nlen} room={room} cells={changed} miss={miss}")
    print("=== sa1 ugui ===")
    for row in patch_ugui(SA1, skip_pids={202, 208}):
        print(" ", row)
    print("=== level1 ugui ===")
    ok = miss = skip = nofit = 0
    for pid, st, old, new in patch_ugui(L1):
        print(f"  pid={pid} {st} {old!r} -> {new!r}")
        if st == "ok":
            ok += 1
        elif st == "miss":
            miss += 1
        elif st == "skip":
            skip += 1
        else:
            nofit += 1
    print(f"level1 ugui ok={ok} miss={miss} skip={skip} nofit={nofit}")


if __name__ == "__main__":
    main()
