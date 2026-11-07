# 自行构建

以正版游戏文件为底，将 `translations.json` 写回 `sharedassets1.assets`：

1. 准备原版 `sharedassets1.assets`（Steam 验证完整性可得）。
2. `scripts/dryrun.py` + `scripts/book_node.pkl` 是 book 对象的解析器；`scripts/splice_book.py` 把译文写入 Text 列（注意：Arg1 的名字标记是引擎查名牌图的键，必须保留日文，脚本内有定案注释）。
3. `scripts/patch_nametext.py` 把角色表里的显示名（NameText）改为中文（与字节等长替换）：忧姬、小夜美、时雨、纱奈姬——回想界面显示的是这个字段。
4. 系统 UI 文本由 `scripts/loc_system_ui.py` 处理。
5. 名牌贴图在 `resources.assets.resS` 内以数据块原地替换，差分块清单见 Release 的 `ress-patch.json`。

脚本中的路径为作者本机路径，使用时请自行调整。
