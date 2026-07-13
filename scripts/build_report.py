# -*- coding: utf-8 -*-
"""TPM 设备管理技能 - 纯文字 MD 产物生成器。

输入：JSON 文件，结构示例：
{
  "module": "am_steps | six_losses | planned_maintenance | opl | inspection | pillars",
  "enterprise": {"company": "", "equipment": "", "line": "", "standard": "", "requirement": ""},
  "content": { ... 各模块可选字段 ... }
}
输出：纯文字 MD 报告（打印到标准输出，或用 -o 写到文件）。
企业专属字段缺失时统一标「待企业补充」。全字段容错，不崩。
"""

import sys
import json
import argparse


def load_input(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": "输入文件读取失败: %s" % e}


def g(data, *keys, default=""):
    """安全取值，任意层级缺失返回 default。"""
    cur = data
    for k in keys:
        if isinstance(cur, dict) and k in cur and cur[k] is not None:
            cur = cur[k]
        else:
            return default
    return cur


def ent(data, key):
    """企业专属字段，缺失标「待企业补充」。"""
    v = g(data, "enterprise", key, default="")
    return v if str(v).strip() else "待企业补充"


def tlist(items, fmt):
    """把列表按 fmt 渲染为 Markdown 行；空列表返回占位。"""
    if not items:
        return "  - 待企业补充"
    out = []
    for it in items:
        if isinstance(it, dict):
            out.append("  - " + fmt(it))
        else:
            out.append("  - " + str(it))
    return "\n".join(out)


# ============ 各模块渲染 ============

def render_six_losses(data):
    c = g(data, "content", default={})
    md = []
    md.append("# 六大损失分析表\n")
    md.append("**企业/范围**：%s ｜ **设备/产线**：%s ｜ **体系要求**：%s\n" % (
        ent(data, "company"), ent(data, "equipment"), ent(data, "requirement")))
    md.append("## 一、损失拆解\n")
    md.append("| 损失类别 | 时长/数量 | 占停机比 | 主要归因 |")
    md.append("|------|------|------|------|")
    losses = g(c, "losses", default=[])
    if not losses:
        md.append("| 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 |")
    else:
        for L in losses:
            md.append("| %s | %s | %s | %s |" % (
                g(L, "category", default="待企业补充"),
                g(L, "amount", default="待企业补充"),
                g(L, "ratio", default="待企业补充"),
                g(L, "cause", default="待企业补充")))
    md.append("")
    md.append("## 二、改善优先级建议\n")
    md.append(tlist(g(c, "priority", default=[]),
                    lambda x: "%s（影响度 %s，可速赢 %s）" % (
                        g(x, "item", default="待企业补充"),
                        g(x, "impact", default="待企业补充"),
                        g(x, "quickwin", default="待企业补充"))))
    md.append("")
    md.append("## 三、对应支柱指向\n")
    md.append(tlist(g(c, "pillars_map", default=[]),
                    lambda x: "%s → %s" % (g(x, "loss", default="待企业补充"),
                                           g(x, "pillar", default="待企业补充"))))
    md.append("")
    return "\n".join(md)


def render_am_steps(data):
    c = g(data, "content", default={})
    cur = g(c, "current_step", default="")
    md = []
    md.append("# 自主保全（AM）七步推进计划卡\n")
    md.append("**企业/范围**：%s ｜ **设备/产线**：%s ｜ **当前所处步骤**：%s\n" % (
        ent(data, "company"), ent(data, "equipment"), cur if cur else "待企业补充"))
    md.append("| 步骤 | 名称 | 核心活动 | 建议周期 | 阶段输出物 | 责任角色 |")
    md.append("|------|------|----------|----------|------------|----------|")
    steps = [
        ("1", "初期清扫", "彻底清扫设备，发现微缺陷（漏油/松动/异音）", "1~3 月", "清扫基准、缺陷清单", "操作工"),
        ("2", "发生源·困难源对策", "消除脏污发生源、改善清扫困难部位", "2~4 月", "发生源/困难源对策表", "操作工+维修"),
        ("3", "制定暂定基准", "操作工自主制定清扫/加油/点检暂定基准", "1~2 月", "暂定基准书", "操作工"),
        ("4", "总点检", "按点检手册对设备各部位总检查", "2~3 月", "总点检记录、技能培训", "维修+操作工"),
        ("5", "自主点检", "步骤3+4 整合为自主点检基准", "1~2 月", "自主点检基准书", "操作工"),
        ("6", "标准化", "设备区段整理整顿、目视化、台账标准化", "持续", "标准化文件、看板", "全员"),
        ("7", "彻底自主管理", "纳入日常，自主定目标持续改善", "持续", "自主管理指标、OPL 积累", "操作工"),
    ]
    for s in steps:
        mark = " ← 当前" if str(cur) == s[0] else ""
        md.append("| %s%s | %s | %s | %s | %s | %s |" % (s[0], mark, s[1], s[2], s[3], s[4], s[5]))
    md.append("")
    md.append("**推进要点**：不可跳步，第 1 步未扫净则后续全虚；操作工为主角，维修为教练；步骤 6 标准化本质是把 5S 固化到设备。\n")
    note = g(c, "note", default="")
    if note:
        md.append("**用户补充/备注**：%s\n" % note)
    return "\n".join(md)


def render_planned_maintenance(data):
    c = g(data, "content", default={})
    md = []
    md.append("# 计划保全（维保计划）\n")
    md.append("**企业/范围**：%s ｜ **设备/产线**：%s ｜ **体系要求**：%s\n" % (
        ent(data, "company"), ent(data, "equipment"), ent(data, "requirement")))
    md.append("## 一、设备分级依据\n")
    md.append("- A 类（关键）：停机损失大、不可替代 → 定期+预知保全")
    md.append("- B 类（重要）：一定影响、可有缓冲 → 定期保全为主")
    md.append("- C 类（一般）：低风险、备件廉价 → 可事后保全\n")
    md.append("## 二、年度维保计划模板\n")
    md.append("| 设备 | 等级 | 保全方式 | 周期 | 预计停机 | 责任 |")
    md.append("|------|------|----------|------|----------|------|")
    annual = g(c, "annual", default=[])
    if not annual:
        md.append("| 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 |")
    else:
        for a in annual:
            md.append("| %s | %s | %s | %s | %s | %s |" % (
                g(a, "equipment", default="待企业补充"),
                g(a, "grade", default="待企业补充"),
                g(a, "method", default="待企业补充"),
                g(a, "cycle", default="待企业补充"),
                g(a, "downtime", default="待企业补充"),
                g(a, "owner", default="待企业补充")))
    md.append("")
    md.append("## 三、月度维保计划模板\n")
    md.append("| 周次 | 设备 | 项目 | 工时 | 配合部门 |")
    md.append("|------|------|------|------|----------|")
    monthly = g(c, "monthly", default=[])
    if not monthly:
        md.append("| 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 |")
    else:
        for m in monthly:
            md.append("| %s | %s | %s | %s | %s |" % (
                g(m, "week", default="待企业补充"),
                g(m, "equipment", default="待企业补充"),
                g(m, "item", default="待企业补充"),
                g(m, "hours", default="待企业补充"),
                g(m, "dept", default="待企业补充")))
    md.append("")
    return "\n".join(md)


def render_opl(data):
    c = g(data, "content", default={})
    md = []
    md.append("# OPL 一点课（One Point Lesson）\n")
    md.append("**企业/范围**：%s ｜ **适用设备/岗位**：%s\n" % (
        ent(data, "company"), ent(data, "equipment")))
    md.append("## 标准结构模板\n")
    md.append("```")
    md.append("【标题】一句话说清这个点")
    md.append("【分类】基础知识 / 改善事例 / 故障事例 / 安全")
    md.append("【对象】适用设备/工序/岗位")
    md.append("【正文】现象/背景 → 要点（图文3~5步） → 正确vs错误做法")
    md.append("【效果】避免了什么 / 提升了多少")
    md.append("【编写】姓名·部门  【日期】")
    md.append("```\n")
    ex = g(c, "example", default={})
    if ex:
        md.append("## 基于用户事例的 OPL 草稿\n")
        md.append("**标题**：%s" % g(ex, "title", default="待企业补充"))
        md.append("**分类**：%s" % g(ex, "category", default="待企业补充"))
        md.append("**对象**：%s" % g(ex, "target", default="待企业补充"))
        md.append("**正文**：%s" % g(ex, "body", default="待企业补充"))
        md.append("**效果**：%s" % g(ex, "effect", default="待企业补充"))
        md.append("**编写**：%s" % g(ex, "author", default="待企业补充"))
        md.append("")
    else:
        md.append("> 提供具体故障/改善事例可生成 OPL 草稿；结构骨架已给，企业专属细节标「待企业补充」。\n")
    return "\n".join(md)


def render_inspection(data):
    c = g(data, "content", default={})
    md = []
    md.append("# 设备点检基准书\n")
    md.append("**企业/范围**：%s ｜ **设备**：%s ｜ **体系要求**：%s\n" % (
        ent(data, "company"), ent(data, "equipment"), ent(data, "requirement")))
    md.append("| 点检项目 | 点检方法 | 工具 | 判定基准 | 周期 | 责任 | 异常处置 |")
    md.append("|----------|----------|------|----------|------|------|----------|")
    items = g(c, "items", default=[])
    if not items:
        md.append("| 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 | 待企业补充 |")
    else:
        for it in items:
            md.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                g(it, "item", default="待企业补充"),
                g(it, "method", default="待企业补充"),
                g(it, "tool", default="待企业补充"),
                g(it, "criteria", default="待企业补充"),
                g(it, "cycle", default="待企业补充"),
                g(it, "owner", default="待企业补充"),
                g(it, "action", default="待企业补充")))
    md.append("")
    md.append("> 判定基准须可量化或可感知，避免「正常」「良好」等空话；与 AM 暂定基准衔接，先暂定后修订为正式。\n")
    return "\n".join(md)


def render_pillars(data):
    c = g(data, "content", default={})
    md = []
    md.append("# 八大支柱方向性引导\n")
    md.append("**企业/范围**：%s\n" % ent(data, "company"))
    pillars = [
        ("1 自主保全 AM", "从初期清扫起步，七步滚动；前提 5S 已就绪"),
        ("2 计划保全 PM", "先建故障履历与设备分级，再定定期/预知策略"),
        ("3 个别改善 FI", "以六大损失为靶子，组跨部门小组攻关"),
        ("4 质量保全 QM", "设备侧消除不良发生源（防错、参数防呆）"),
        ("5 教育训练", "按设备·品质·保全三技能矩阵培训，OPL 为主载体"),
        ("6 初期管理 MP", "新设备导入前置维修性/可操作性/易清扫性"),
        ("7 事务改善", "间接部门流程提速，避免支撑瓶颈"),
        ("8 安全卫生环境", "所有活动以零灾害为底线前置约束"),
    ]
    md.append("| 支柱 | 推进要点 |")
    md.append("|------|----------|")
    for p in pillars:
        md.append("| %s | %s |" % p)
    md.append("")
    md.append("**从哪开始**：先 5S → AM 步骤 1 → 同步建 PM 故障履历 → 选 1~2 台示范机。\n")
    md.append("**推不动排查**：高层未背书 / 跳了 AM 清扫步 / 只靠维修部门单打。\n")
    note = g(c, "note", default="")
    if note:
        md.append("**用户补充/备注**：%s\n" % note)
    md.append("> 本文件仅作方向引导，正式部署需结合企业成熟度，本技能不代出推进方案。\n")
    return "\n".join(md)


RENDERERS = {
    "six_losses": render_six_losses,
    "am_steps": render_am_steps,
    "planned_maintenance": render_planned_maintenance,
    "opl": render_opl,
    "inspection": render_inspection,
    "pillars": render_pillars,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="输入 JSON 路径")
    ap.add_argument("-o", "--output", help="输出 MD 路径（省略则打印）", default=None)
    args = ap.parse_args()

    data = load_input(args.input)
    if "_error" in data:
        out = "# 生成失败\n\n%s\n" % data["_error"]
    else:
        module = g(data, "module", default="")
        renderer = RENDERERS.get(module)
        if renderer:
            out = renderer(data)
        else:
            out = "# 模块未识别\n\n未知 module: %s\n可选: %s\n" % (
                module if module else "(空)", " / ".join(RENDERERS.keys()))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print("已生成: %s" % args.output)
    else:
        print(out)


if __name__ == "__main__":
    main()
