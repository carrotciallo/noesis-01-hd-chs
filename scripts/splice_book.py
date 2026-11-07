"""splice 回写：把 book 记录替换为翻译后载荷（原地，尾部补零到原尺寸）。
  1) 备份原文件 -> /tmp/noesis/backup/sharedassets1.assets.orig
  2) parse -> 应用 translations.json 全部 key -> write_node 序列化
  3) pad 到原 byte_size -> 写回 [byte_start, byte_start+size)
  4) 验证：重开 UnityPy 重解析，核对替换数、总长、对象完整性
用法:  python3 splice_book.py [--verify-only]
"""
import struct, json, sys, time, shutil
sys.path.insert(0, "/tmp/noesis")
import dryrun as D

SA1 = D.SA1
BAK = "/tmp/noesis/backup/sharedassets1.assets.orig"
TRANS = "/tmp/noesis/noesis-port/loc-work/translations.json"

# Arg1 speaker tags. Do not touch col3 "名前".
# 2026-11-08 实机定案: Arg1 的【…】是引擎查名牌图的键, 必须留日文 —— 映射成中文后
# 查不到图, 名牌整块不显示 (9 月版起一直如此, 当时没实机验)。玩家看到的名牌是
# 重绘贴图 (nam_* 里已画中文名), 所以 NAME_MAP 只作译名对照、不再生效。
NAME_MAP = {
    "【時雨】": "【时雨】",
    "【千夜】": "【千夜】",
    "【こよみ】": "【小夜美】",
    "【こよみ？】": "【小夜美？】",
    "【こよも】": "【小夜美】",
    "【憂姫】": "【忧姬】",
    "【一夜】": "【一夜】",
    "【一夜？】": "【一夜？】",
    "【遥】": "【遥】",
    "【クエデア】": "【珂蒂娅】",
    "【さなぎ】": "【纱奈姬】",
    "【上級生】": "【高年级生】",
    "【私】": "【我】",
    "【少女A】": "【少女A】",
    "【少女】": "【少女】",
    "【女子】": "【女生】",
    "【？？】": "【？？】",
}

def main():
    verify_only = "--verify-only" in sys.argv
    if not verify_only:
        import os
        os.makedirs("/tmp/noesis/backup", exist_ok=True)
        if not os.path.exists(BAK):
            shutil.copy2(SA1, BAK)
            print("backup -> %s" % BAK, flush=True)
        else:
            print("backup exists (not overwriting)", flush=True)

    node = D.load_node()
    import UnityPy
    env = UnityPy.Environment()
    f = env.load_file(SA1)
    book = [o for o in f.objects.values() if o.byte_size > 1000000 and o.class_id == 114][0]
    bs, bsz = book.byte_start, book.byte_size
    raw = book.get_raw_data()
    assert len(raw) == bsz
    print("book record: [%#x, %#x) size=%#x" % (bs, bs + bsz, bsz), flush=True)

    r = D.R(raw)
    val = D.rd(node, r)
    # orig: r.p==bsz (tight). re-splice of an already-padded record: r.p<=bsz, remainder zeros.
    assert r.p <= bsz, "parse overflow: %d > %d" % (r.p, bsz)
    tail = raw[r.p:]
    assert all(b == 0 for b in tail), "non-zero tail %d bytes at r.p=%d" % (len(tail), r.p)
    print("parse end=%d record size=%d (tail zero-pad %d)" % (r.p, bsz, len(tail)), flush=True)
    valc = D.clean(val)

    # Speaker tags must be mapped from the Japanese original, not from a
    # previous splice (【少女A】 once collapsed to 【少女】 cannot be undone).
    env_o = UnityPy.Environment()
    f_o = env_o.load_file(BAK)
    book_o = [o for o in f_o.objects.values() if o.byte_size > 1000000 and o.class_id == 114][0]
    r_o = D.R(book_o.get_raw_data())
    orig_grids = D.clean(D.rd(node, r_o)).get("importGridList") or []

    trans = json.load(open(TRANS, encoding="utf-8"))
    grids = valc.get("importGridList") or []
    replaced = 0
    names_n = 0
    miss_keys = 0
    for gi, g in enumerate(grids):
        nm = g.get("name") or ""
        base = nm.rsplit(":", 1)[-1] if ":" in nm else nm
        rows = g.get("rows") or []
        orows = (orig_grids[gi].get("rows") or []) if gi < len(orig_grids) else []
        for idx, row in enumerate(rows):
            st = row.get("strings") or []   # in-place: keep original length
            uid = "%s:%d" % (base, idx)
            # row 0 is the Utage column header; engine looks up "Text" by name.
            if idx == 0:
                if len(st) > 8:
                    st[8] = "Text"
                continue
            # speaker plate above the message box lives in Arg1, not Text.
            ost = ((orows[idx].get("strings") or []) if idx < len(orows) else [])
            src_name = ost[1] if len(ost) > 1 else (st[1] if len(st) > 1 else "")
            if False and src_name in NAME_MAP and len(st) > 1:  # 名牌查表键, 见上方定案
                st[1] = NAME_MAP[src_name]
                names_n += 1
            if uid in trans and len(st) > 8 and (st[8] or ""):
                st[8] = trans[uid]          # mutates the list held by row
                replaced += 1
    print("cells replaced: %d (translation units: %d) names: %d" % (replaced, len(trans), names_n), flush=True)

    w = D.W()
    D.wn(w, node, valc)
    new = bytes(w.b)
    if len(new) > bsz:
        print("FATAL: new larger than record (%d > %d)" % (len(new), bsz), flush=True)
        sys.exit(1)
    padded = new + b"\x00" * (bsz - len(new))
    assert len(padded) == bsz

    if not verify_only:
        d = bytearray(open(SA1, "rb").read())
        d[bs:bs + bsz] = padded
        open(SA1, "wb").write(bytes(d))
        print("spliced %d bytes at %#x; file size %d" % (len(padded), bs, len(d)), flush=True)

    # ---- verify ----
    env2 = UnityPy.Environment()
    f2 = env2.load_file(SA1)
    print("reload OK: %d objects" % len(f2.objects), flush=True)
    book2 = [o for o in f2.objects.values() if o.byte_size > 1000000 and o.class_id == 114][0]
    assert book2.byte_start == bs and book2.byte_size == bsz
    raw2 = book2.get_raw_data()
    # original record bytes for non-book area must be identical
    d0 = open(BAK if not verify_only else SA1, "rb").read()
    d1 = open(SA1, "rb").read()
    same_prefix = d0[:bs] == d1[:bs]
    same_suffix = d0[bs + bsz:] == d1[bs + bsz]
    print("verify: prefix identical=%s suffix identical=%s filelen %d -> %d"
          % (same_prefix, same_suffix, len(d0), len(d1)), flush=True)
    r2 = D.R(raw2)
    v2 = D.rd(node, r2)
    # count CJK cells in Text column now
    cjk = 0; jpn = 0
    import re as _re
    for g in v2.get("importGridList") or []:
        for row in (g.get("rows") or []):
            st = (row.get("strings") or []) + [""] * 12
            t = st[8] or ""
            if _re.search(r"[\u4e00-\u9fff]", t): cjk += 1
            if _re.search(r"[\u3040-\u30ff]", t): jpn += 1
    print("verify: Text cells with CJK Han: %d, with kana (untranslated JP): %d" % (cjk, jpn), flush=True)
    # sample a few translated rows
    print("verify samples:")
    for uid, want in (("chiya01z:251", "滴答"), ("koyomi:7057", None), ("yuki:9994", None), ("sanagi:0", None)):
        base, i = uid.split(":")
        for g in v2.get("importGridList") or []:
            nm = g.get("name") or ""
            if nm.rsplit(":", 1)[-1] == base:
                st = ((g.get("rows") or [None] * (int(i) + 1))[int(i)] or {}).get("strings") or []
                print("  %s: %r" % (uid, (st[8] or "")[:60]))
                break
    print("DONE", flush=True)

if __name__ == "__main__":
    main()
