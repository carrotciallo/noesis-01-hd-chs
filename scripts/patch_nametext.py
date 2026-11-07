"""把角色表 (sharedassets1 内对象 202) 的 NameText 显示名改为中文。
CharacterName 是查表键 (名牌图/角色解析) 必须留日文; NameText 只用于回想等
文本显示。四个名字中日恰好等字节长, 原地替换不动文件大小与任何偏移。
用法: python3 patch_nametext.py <sharedassets1.assets>  (原地修改, 请先备份)
"""
import sys

PAIRS = [("【憂姫】", "【忧姬】"), ("【こよみ】", "【小夜美】"),
         ("【時雨】", "【时雨】"), ("【さなぎ】", "【纱奈姬】")]

def main(path):
    data = bytearray(open(path, "rb").read())
    for jp, zh in PAIRS:
        jb, zb = jp.encode(), zh.encode()
        assert len(jb) == len(zb)
        hits, i = [], 0
        while True:
            i = data.find(jb, i)
            if i < 0: break
            hits.append(i); i += 1
        pair = [h for h in hits if b"kara.png" in data[h + len(jb):h + len(jb) + 80]
                or b"Icon/nam_" in data[h + len(jb):h + len(jb) + 200]]
        assert len(pair) == 2, (jp, pair)
        data[pair[1]:pair[1] + len(jb)] = zb  # 第二个是 NameText
        print(jp, "->", zh, "at", pair[1])
    open(path, "wb").write(data)

if __name__ == "__main__":
    main(sys.argv[1])
