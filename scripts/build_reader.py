#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_reader.py — 古籍共读网站通用构建引擎
============================================================
读取「项目目录」下的 config.json 与若干数据 JSON，将 token 化的
reader-template.html 渲染为自包含的单文件 index.html。

用法:
    python3 build_reader.py <project_dir> [--out <dist/index.html>]

项目目录结构（数据文件全部可选，至少要有 chapters.json）:
    config.json         必需：书名、key、官网、主题色等
    chapters.json       必需：[{n, label, text}]  每章原文
    sentences.json      可选：{ "1": [[原文, 译文], ...] }  逐句对照
    content.json        可选：{ "1": {zhu, chuan, jingzheng, jiedu, dao} }  章内详解
    study.json          可选：结构脉络/概念词典/名句/安心签/当代焦虑
    p1.json            可选：参考书目/人物/省察问/章间呼应
    p2.json            可选：朱注/四书互参/以经解经专题
    pinyin.json        可选：{"PINYIN":{...},"TONGGJIA":{...},"PHRASE":{...}}

输出: 单文件 index.html（自包含，可直接用浏览器打开，或托管到任意静态空间）。
"""
import json, os, sys, html as htmlmod, base64, re
from datetime import date, timedelta

# ------------------------- 中文数字 -------------------------
CN_UNIT = ['', '十', '百', '千']
CN_DIG = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']

def cn_num(n):
    """1..9999 的中文数字。"""
    if n <= 0:
        return '零'
    s = str(n)
    out = []
    L = len(s)
    for i, ch in enumerate(s):
        d = int(ch)
        pos = L - i - 1
        if d == 0:
            if out and out[-1] != '零':
                out.append('零')
            continue
        if pos % 4 == 1 and d == 1 and i == 0 and L > 1:
            # 「十」开头省略「一」
            out.append('十')
        else:
            if pos % 4 == 1:
                out.append(CN_DIG[d] + '十')
            elif pos % 4 == 2:
                out.append(CN_DIG[d] + '百')
            elif pos % 4 == 3:
                out.append(CN_DIG[d] + '千')
            else:
                out.append(CN_DIG[d])
        if pos >= 4:
            out.append('万' if pos < 8 else '亿')
    return ''.join(out).replace('零零', '零').strip('零')

def gen_cn(total):
    return [cn_num(i) for i in range(1, total + 1)]

# ------------------------- 注音 / 通假 -------------------------
def load_pinyin(path):
    PINYIN, TONGGJIA, PHRASE = {}, {}, {}
    if path and os.path.exists(path):
        d = json.load(open(path, encoding='utf-8'))
        PINYIN = d.get('PINYIN', {})
        TONGGJIA = d.get('TONGGJIA', {})
        PHRASE = d.get('PHRASE', {})
    return PINYIN, TONGGJIA, PHRASE

def annotate(s, PINYIN, TONGGJIA, PHRASE):
    """生僻/特殊字加 ruby 注音；通假字加虚线 + title 提示。"""
    out = []
    i, N = 0, len(s)
    while i < N:
        matched = False
        for L in (2,):
            if i + L <= N:
                ph = s[i:i + L]
                if ph in PHRASE:
                    py, note = PHRASE[ph]
                    t = note.replace('"', '&quot;')
                    out.append('<ruby class="tj" title="%s">%s<rt>%s</rt></ruby>' % (t, ph, py))
                    i += L
                    matched = True
                    break
        if matched:
            continue
        ch = s[i]
        if ch in PINYIN or ch in TONGGJIA:
            py = PINYIN.get(ch, '')
            note = TONGGJIA.get(ch, '')
            rt = '<rt>%s</rt>' % py if py else ''
            if note:
                t = note.replace('"', '&quot;')
                out.append('<ruby class="tj" title="%s">%s%s</ruby>' % (t, ch, rt))
            else:
                out.append('<ruby>%s%s</ruby>' % (ch, rt))
        else:
            out.append(ch)
        i += 1
    return ''.join(out)

# ------------------------- 工具 -------------------------
def esc(s):
    return htmlmod.escape(s, quote=False)

def fmt_cn(d):
    return '%d月%d日' % (d.month, d.day)

# ------------------------- 章内详解（七标签） -------------------------
def detail_html(n, chapters_text, CONTENT, SENT, P1, P2, SCHOOL_INTRO, BASIS, PINYIN, TONGGJIA, PHRASE):
    c = CONTENT.get(str(n), {})
    # 译文
    yi = '<p class="nodata">（暂无对照译文）</p>'
    pairs = SENT.get(str(n))
    if pairs:
        rows = []
        for orig, trans in pairs:
            o = annotate(esc(orig), PINYIN, TONGGJIA, PHRASE)
            t = esc(trans)
            rows.append('<div class="srow"><div class="src">%s</div><div class="tr">%s</div></div>' % (o, t))
        yi = '<div class="sentences">%s</div>' % ''.join(rows)
    # 注释
    zhu = ''.join('<li><b>%s</b>　%s</li>' % (esc(t), esc(note)) for t, note in c.get('zhu', []))
    zhu = '<ul class="zhu">%s</ul>' % zhu if zhu else '<p class="nodata">（暂无）</p>'
    # 串讲 + 经证链
    chuan_ps = [p for p in c.get('chuan', '').split('\n') if p.strip()]
    chuan_base = ''.join('<p>%s</p>' % esc(p) for p in chuan_ps) if chuan_ps else '<p class="nodata">（暂无串讲）</p>'
    jz = c.get('jingzheng', [])
    if jz:
        jz_items = ''.join(
            '<li><span class="jzbook">%s</span><span class="jzpass">%s</span><span class="jznote">%s</span></li>'
            % (esc(b), esc(p), esc(note)) for b, p, note in jz)
        chuan = chuan_base + '<div class="jzchain"><div class="jzhead">经证链 · 以经典解经典</div><ul class="jzlist">%s</ul></div>' % jz_items
    else:
        chuan = chuan_base
    # 朱注
    zz = (P2.get('zhuzhu', {}) or {}).get(str(n), '')
    if zz:
        first_sent = ''
        for _d in chapters_text:
            if _d['n'] == n:
                _t = _d['text']
                first_sent = (_t.split('。')[0] + '。') if _t else ''
                break
        zz_head = '<p class="zz-head">首在：<span class="zz-ref">%s</span></p>' % esc(first_sent) if first_sent else ''
        zz_html = zz_head + '<p class="zz">%s</p>' % esc(zz)
    else:
        zz_html = '<p class="nodata">（暂无）</p>'
    # 解读
    jd = c.get('jiedu', [])
    jd_rows = []
    for item in jd:
        lab = item.get('label', '')
        intro = esc(item['intro']) if item.get('intro') else esc(SCHOOL_INTRO.get(lab, ''))
        intro_html = '<div class="jintro">%s</div>' % intro if intro else ''
        basis = ('<span class="jbasis">所本：%s</span>' % esc(item.get('basis', BASIS.get(lab, '')))) if (item.get('basis') or lab in BASIS) else ''
        jd_rows.append(
            '<div class="jrow"><button type="button" class="jlabel" aria-expanded="false">%s</button>'
            '<div class="jbody">%s%s<p>%s</p></div></div>'
            % (esc(lab), basis, intro_html, esc(item.get('text', ''))))
    jiedu = ('<p class="jhint">学派/视角名称可点击，展开简介</p>' + ''.join(jd_rows)) if jd_rows else '<p class="nodata">（暂无）</p>'
    jiedu = '<div class="jiedu">%s</div>' % jiedu
    # 导读
    dao = '<p>%s</p>' % esc(c['dao']) if c.get('dao') else '<p class="nodata">（暂无）</p>'
    # 省察
    sheng = (P1.get('reflections', {}) or {}).get(str(n)) or c.get('sheng')
    if sheng:
        sheng_items = ''.join('<li>%s</li>' % esc(q) for q in sheng)
        sheng_html = (
            '<div class="sheng-wrap">'
            '<ol class="sheng">%s</ol>'
            '<div class="sheng-note-box">'
            '<label class="sheng-lab">我的践行笔记 <span class="sheng-count" id="shengCount-%d">0</span> 字</label>'
            '<textarea class="sheng-note" id="shengNote-%d" data-n="%d" rows="3" placeholder="把今天的体悟写下来：哪一句戳中你？你打算怎么用？"></textarea>'
            '</div></div>' % (sheng_items, n, n, n))
    else:
        sheng_html = '<p class="nodata">（暂无）</p>'

    # 动态标签：仅渲染有内容的面板，保持 UI 一致
    tabs = []  # (key, label, html)
    if pairs:
        tabs.append(('yi', '译文', yi))
    if c.get('zhu'):
        tabs.append(('zhu', '注释', zhu))
    if c.get('chuan') or jz:
        tabs.append(('chuan', '串讲', chuan))
    if zz:
        tabs.append(('zz', '朱注', zz_html))
    if jd:
        tabs.append(('jiedu', '解读', jiedu))
    if c.get('dao'):
        tabs.append(('dao', '导读', dao))
    tabs.append(('sheng', '省察', sheng_html))

    btns = ''.join('<button class="tab-btn%s" data-tab="%s">%s</button>' % (' active' if i == 0 else '', k, lab)
                   for i, (k, lab, _) in enumerate(tabs))
    pans = ''.join('<div class="panel%s" data-panel="%s">%s</div>' % (' active' if i == 0 else '', k, h)
                   for i, (k, lab, h) in enumerate(tabs))
    return (
        '    <div class="det">\n'
        '      <div class="det-label">本章详解</div>\n'
        '      <div class="tabs" role="tablist">%s</div>\n'
        '      <div class="panels">%s</div>\n'
        '    </div>' % (btns, pans))

# ------------------------- 静态目录 / 章节 -------------------------
def build_chapters(data, CN, BUILD_TODAY, CONTENT, SENT, P1, P2, SCHOOL_INTRO, BASIS, PINYIN, TONGGJIA, PHRASE):
    toc, articles = [], []
    for i, d in enumerate(data):
        dt = BUILD_TODAY + timedelta(days=i)
        toc.append(
            '      <li><a href="#ch-%d" data-n="%d">'
            '<span class="seal">%s</span>'
            '<span class="t">%s</span>'
            '<span class="d">第%d天 · %s</span></a></li>'
            % (d['n'], d['n'], CN[i], esc(d['label']), d['n'], fmt_cn(dt)))
        paras_html = ''.join('<p>%s</p>' % annotate(esc(p), PINYIN, TONGGJIA, PHRASE) for p in d['paras'])
        articles.append(
            '  <article class="chapter view" id="ch-%d" data-chapter="%d" data-view="ch">\n'
            '    <div class="ch-head"><span class="seal seal-lg">%s</span>\n'
            '      <div><h2>第%s章</h2><p class="lab">%s</p></div>\n'
            '      <span class="spacer"></span>\n'
            '      <button class="btn ghost share-btn" data-n="%d" title="复制本章链接，分享给书友即可直达本章">分享本章</button></div>\n'
            '    <div class="ch-text">%s</div>\n'
            '    <div class="ch-foot"><a href="#toc">回到目录</a></div>\n'
            '%s\n'
            '  </article>'
            % (d['n'], d['n'], CN[i], CN[i], esc(d['label']), d['n'], paras_html,
               detail_html(d['n'], data, CONTENT, SENT, P1, P2, SCHOOL_INTRO, BASIS, PINYIN, TONGGJIA, PHRASE)))
    return '\n'.join(toc), '\n'.join(articles)

# ------------------------- 研读 hub -------------------------
def study_html(STUDY, P1, P2, CN, SEGMENTS):
    def seg_of(n):
        n = int(n)
        for th, lab in SEGMENTS or []:
            if n <= th:
                return lab
        return ''
    out = []
    # 一、结构脉络
    struct = STUDY.get('structure', [])
    sr = []
    for i, row in enumerate(struct, 1):
        name, rng, desc, key = (list(row) + ['', '', '', ''])[:4]
        skey = '<p class="skey"><b>重点：</b>%s</p>' % esc(key) if key else ''
        sr.append('<div class="snode"><div class="snum">%d</div><div class="sbody"><div class="sname">%s <span class="srange">%s</span></div><p class="sdesc">%s</p>%s</div></div>'
                  % (i, esc(name), esc(rng), esc(desc), skey))
    out.append(('一、全书结构脉络', '<div class="smap">%s</div>' % ''.join(sr)))
    # 二、核心概念词典
    concepts = STUDY.get('concepts', [])
    cc = []
    for row in concepts:
        term = row[0]
        defi = row[2] if len(row) > 2 else ''
        srcchap = row[3] if len(row) > 3 else ''
        occ = row[4] if len(row) > 4 and isinstance(row[4], list) else []
        chaps = [c for c in srcchap.split(',') if c] if srcchap else []
        links = ' · '.join('<a class="citem" href="#ch-%s">第%s章</a>' % (c, CN[int(c) - 1]) for c in chaps)
        cchap = '<div class="cchap">出处：%s</div>' % links if links else ''
        occ_html = ''
        if occ:
            oi = []
            for och, osent in occ:
                try:
                    och_lbl = CN[int(och) - 1]
                except Exception:
                    och_lbl = och
                oi.append('<li><a class="citem" href="#ch-%s">第%s章</a><span class="osent">%s</span></li>' % (och, och_lbl, esc(osent)))
            occ_html = '<div class="occ"><div class="occ-head">经典互见</div><ul class="occlist">%s</ul></div>' % ''.join(oi)
        cc.append('<div class="concept"><div class="cterm">%s</div><p class="cdef">%s</p>%s%s</div>' % (esc(term), esc(defi), cchap, occ_html))
    out.append(('二、核心概念词典', '<div class="cgrid">%s</div>' % ''.join(cc)))
    # 三、名句摘录
    quotes = STUDY.get('quotes', [])
    qq = []
    for row in quotes:
        q, ch, ctx = (list(row) + ['', '', ''])[:3]
        ctx_html = '<div class="qctx">%s</div>' % esc(ctx) if ctx else ''
        qq.append('<li><span class="qtext">%s</span> <a class="qchap" href="#ch-%s">— 第%s章</a>%s</li>' % (esc(q), ch, CN[int(ch) - 1], ctx_html))
    out.append(('三、名句摘录', '<ul class="qlist">%s</ul>' % ''.join(qq)))
    # 四、参考书目
    bib = P1.get('bibliography', [])
    bib_html = '<ol class="bib">%s</ol>' % ''.join('<li><span class="bname">%s</span><p>%s</p></li>' % (esc(t), esc(desc)) for t, desc in bib) if bib else '<p class="nodata">（暂无）</p>'
    out.append(('四、参考书目', bib_html))
    # 五、人物小传
    figs = P1.get('figures', [])
    fig_html = '<div class="figrid">%s</div>' % ''.join('<div class="fig"><div class="fname">%s <span class="ftitle">%s</span></div><p>%s</p></div>' % (esc(name), esc(title), esc(desc)) for name, title, desc in figs) if figs else '<p class="nodata">（暂无）</p>'
    out.append(('五、人物小传', fig_html))
    # 六、章间呼应 + 义理脊柱
    spine = STUDY.get('spine', [])
    sp_nodes = []
    for name, rng, desc in spine:
        sp_nodes.append('<div class="spnode"><div class="spname">%s</div><div class="sprange">%s</div><p class="spdesc">%s</p></div>' % (esc(name), esc(rng), esc(desc)))
    spine_html = '<div class="spine">%s</div>' % ''.join(sp_nodes) if sp_nodes else ''
    echoes = P1.get('echoes', [])
    ech_rows = []
    for row in echoes:
        chn, theme, links, note = (list(row) + ['', '', '', ''])[:4]
        lk = ' · '.join('<a class="citem" href="#ch-%s">第%s章</a>' % (c, CN[int(c) - 1]) for c in links.split(',') if c)
        badge = '<span class="seg">%s</span>' % seg_of(chn) if seg_of(chn) else ''
        ech_rows.append('<tr><td><a class="citem" href="#ch-%s">第%s章</a></td><td>%s%s</td><td>%s</td><td>%s</td></tr>'
                        % (chn, CN[int(chn) - 1], badge, esc(theme), lk, esc(note)))
    echo_html = '<div class="ech-wrap"><table class="ech"><thead><tr><th>章</th><th>要旨</th><th>呼应章</th><th>说明</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(ech_rows) if ech_rows else '<p class="nodata">（暂无）</p>'
    out.append(('六、章间呼应 · 义理脊柱', spine_html + echo_html))
    # 七、四书互参（以 p2.sishu 表示，命名可泛化为「互参」）
    sishu = P2.get('sishu', [])
    ss_cards = []
    for i, item in enumerate(sishu):
        zh = item.get('zh', '')
        theme = item.get('theme', '')
        refs = item.get('refs', [])
        ref_items = ''.join('<li><span class="sbook">%s</span><span class="spass">%s</span><span class="snote">%s</span></li>' % (esc(r.get('book', '')), esc(r.get('passage', '')), esc(r.get('note', ''))) for r in refs)
        ss_cards.append('<div class="sscard" id="sishu-%d"><div class="sshead"><span class="sszh">%s</span><span class="sstheme">%s</span></div><ul class="ssrefs">%s</ul></div>' % (i, esc(zh), esc(theme), ref_items))
    sishu_html = '<div class="ssgrid">%s</div>' % ''.join(ss_cards) if ss_cards else '<p class="nodata">（暂无）</p>'
    chap_idx = {str(i): [] for i in range(1, len(CN) + 1)}
    for i, item in enumerate(sishu):
        for c2 in item.get('chaps', []):
            if str(c2) in chap_idx:
                chap_idx[str(c2)].append(i)
    idx_rows = []
    for i in range(1, len(CN) + 1):
        refs = chap_idx[str(i)]
        if not refs:
            continue
        items = ' · '.join('<a class="citem" href="#sishu-%d">%s</a>' % (r, esc(sishu[r].get('zh', ''))) for r in refs)
        idx_rows.append('<li><span class="idxch">第%s章</span> %s</li>' % (CN[i - 1], items))
    sishu_index = '<div class="ssidx"><div class="ssidx-head">逐章对应</div><ul class="ssidxlist">%s</ul></div>' % ''.join(idx_rows) if idx_rows else ''
    if ss_cards or idx_rows:
        out.append(('七、经典互参', sishu_index + sishu_html))
    # 八、以经解经专题
    topics = P2.get('topics', [])
    tp = []
    for t in topics:
        name = t.get('name', ''); desc = t.get('desc', ''); ps = t.get('passages', [])
        pli = []
        for ch, sent, note in ps:
            try:
                chlbl = CN[int(ch) - 1]
            except Exception:
                chlbl = ch
            pli.append('<li><a class="citem" href="#ch-%s">第%s章</a><span class="tsent">%s</span><span class="tnote">%s</span></li>' % (ch, chlbl, esc(sent), esc(note)))
        tp.append('<div class="topic"><div class="tname">%s</div><p class="tdesc">%s</p><ul class="tlist">%s</ul></div>' % (esc(name), esc(desc), ''.join(pli)))
    if tp:
        out.append(('八、以经解经专题', '<div class="topicgrid">%s</div>' % ''.join(tp)))
    # 九、当代焦虑 / 现代处境（可选，数据键 modern_anxiety 或 modern）
    mx = STUDY.get('modern_anxiety') or STUDY.get('modern', [])
    if mx:
        mx_cards = []
        for it in mx:
            mx_cards.append('<div class="mxcard"><div class="mxhead"><span class="mxseg">%s</span></div><p class="mxstress"><b>现代处境</b>　%s</p><p class="mxremedy">%s</p><blockquote class="mxquote">%s</blockquote></div>'
                            % (esc(it.get('theme', '')), esc(it.get('stress', '')), esc(it.get('remedy', '')), esc(it.get('quote', ''))))
        out.append(('九、经典义理与现代处境', '<div class="mxgrid">%s</div>' % ''.join(mx_cards)))
    # 十、引用与出处说明
    cite = STUDY.get('cite') or ('本阅读器所收原文与引文，均出自进入<b>公有领域的古代典籍</b>，不含现代出版物受版权保护的文字；各类疏通、说明文字均为本阅读器自撰，未摘引任何现代著作原文。')
    cite_html = '<div class="citebox"><p>%s</p></div>' % cite
    out.append(('十、引用与出处说明', cite_html))

    blocks = '\n'.join(
        '    <div class="study-block">\n      <h3 class="blk-title">%s</h3>\n      %s\n    </div>' % (title, body)
        for title, body in out)
    return (
        '  <section class="study view" id="study" data-view="study">\n'
        '    <div class="study-head"><h2>研 读</h2>\n'
        '      <p class="study-sub">结构脉络 · 核心概念 · 名句摘录 · 省察与呼应 · 经典互参 · 以经解经专题——先立其大，再入章句</p></div>\n'
        '%s\n'
        '  </section>' % blocks)

# ------------------------- favicon（印章风） -------------------------
def make_favicon(char, theme):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#b2302b"/><stop offset="1" stop-color="#8a1f1f"/></linearGradient></defs>'
        '<rect x="4" y="4" width="56" height="56" rx="12" fill="url(#g)"/>'
        '<rect x="9" y="9" width="46" height="46" rx="8" fill="none" stroke="#ffffff" stroke-opacity="0.55" stroke-width="1.5"/>'
        '<text x="32" y="44" font-size="38" text-anchor="middle" fill="#ffffff" '
        'font-family="STSong, SimSun, serif">%s</text></svg>' % char)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return 'data:image/svg+xml;base64,' + b64

# ------------------------- 主流程 -------------------------
def main():
    if len(sys.argv) < 2:
        print("用法: python3 build_reader.py <project_dir> [--out <dist/index.html>]")
        sys.exit(1)
    proj = sys.argv[1]
    out = None
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    cfg = json.load(open(os.path.join(proj, 'config.json'), encoding='utf-8'))
    def load(name, default=None):
        p = os.path.join(proj, name)
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8'))
        return default
    chapters = load('chapters.json', [])
    assert chapters, "chapters.json 缺失或为空"
    CONTENT = load('content.json', {}) or {}
    SENT = load('sentences.json', {}) or {}
    STUDY = load('study.json', {}) or {}
    P1 = load('p1.json', {}) or {}
    P2 = load('p2.json', {}) or {}
    PINYIN, TONGGJIA, PHRASE = load_pinyin(os.path.join(proj, 'pinyin.json'))

    book = cfg['book']
    key = cfg.get('key', re.sub(r'[^a-z0-9]', '', book.lower()) or 'book')
    favchar = cfg.get('favchar', book[0])
    theme = cfg.get('theme', '#a02c2c')
    share_base = cfg.get('share_base', '')
    SCHOOL_INTRO = cfg.get('schools', {})
    BASIS = cfg.get('basis', {})
    SEGMENTS = cfg.get('segments')
    BUILD_TODAY = date.today()

    # 章节分段：content 可带 paras，否则整段
    for d in chapters:
        if 'paras' not in d:
            d['paras'] = [d['text']]
    total = len(chapters)
    CN = gen_cn(total)
    total_cn = cn_num(total)

    toc_items, chapters_html = build_chapters(chapters, CN, BUILD_TODAY, CONTENT, SENT, P1, P2, SCHOOL_INTRO, BASIS, PINYIN, TONGGJIA, PHRASE)
    study_html_out = study_html(STUDY, P1, P2, CN, SEGMENTS)

    # 模板
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'reader-template.html')
    if not os.path.exists(tpl_path):
        tpl_path = os.path.join(proj, 'reader-template.html')
    tpl = open(tpl_path, encoding='utf-8').read()

    favicon = make_favicon(favchar, theme)
    intro = cfg.get('intro', '%s共读 · 一天一章，循序渐进。' % book)
    subtitle = cfg.get('subtitle', '')
    sidebar_foot = cfg.get('sidebar_foot', '一天一章 · %s天<br>文本依据：%s<br>虚线标注的字为通假 / 异读，点按可看说明' % (total_cn, book))
    footer_cite = cfg.get('footer_cite', '文本依据：公有领域古籍底本，译文、串讲、解读等均为编者自撰。')
    footer_slogan = cfg.get('footer_slogan', '%s共读 · 一天一章 · %s天' % (book, total_cn))

    html = (tpl
            .replace('{{BOOK}}', book)
            .replace('{{TOTAL_CN}}', total_cn)
            .replace('{{KEY}}', key)
            .replace('{{FAVICON}}', favicon)
            .replace('{{THEME}}', theme)
            .replace('{{INTRO}}', intro)
            .replace('{{SUBTITLE}}', subtitle)
            .replace('{{SIDEBAR_FOOT}}', sidebar_foot)
            .replace('{{FOOTER_CITE}}', footer_cite)
            .replace('{{FOOTER_SLOGAN}}', footer_slogan)
            .replace('__TOTAL__', str(total))
            .replace('__CN__', json.dumps(CN, ensure_ascii=False))
            .replace('__DATA__', json.dumps(chapters, ensure_ascii=False))
            .replace('__TOC_ITEMS__', toc_items)
            .replace('__CHAPTERS_HTML__', chapters_html)
            .replace('__STUDY_HTML__', study_html_out)
            .replace('__ANSHEN__', json.dumps(STUDY.get('anshen', []), ensure_ascii=False))
            .replace('__SHENGQ__', json.dumps(P1.get('reflections', {}), ensure_ascii=False))
            .replace("'__SHARE_BASE__'", "'%s'" % share_base))

    if out is None:
        out = os.path.join(proj, 'dist', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    print('[OK] %s (%d bytes, %d 章)' % (out, len(html.encode('utf-8')), total))

if __name__ == '__main__':
    main()
