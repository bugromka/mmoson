# -*- coding: utf-8 -*-
"""
Проверка читаемости рисунков ММОСО'Н.

Ловит два рода дефектов:
  1) текст на текст  — подпись налезает на подпись;
  2) текст на данные — подпись лежит поверх столбца, линии, сектора или заливки.

Второй род — тот, что был пропущен в первой версии проверки: она сравнивала
только подписи между собой. Здесь текст проверяется против отрендеренного
изображения самих данных: фигура рисуется дважды — со скрытым текстом и
целиком, — и под каждой подписью считается доля непустых (не белых) пикселей.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import importlib
import figures as F

TEXT_ON_TEXT = 0.12   # доля перекрытия подписей, выше которой считаем дефектом
BUSY_LIMIT   = 0.10   # доля пикселей, отличных от преобладающего фона


def capture(idx):
    """Строит фигуру номер idx, не сохраняя её, и возвращает объект Figure."""
    importlib.reload(F)
    holder = {}
    orig = F.save

    def cap(fig, name):
        holder['fig'] = fig
        return name

    F.save = cap
    try:
        getattr(F, f'fig{idx:02d}')()
    finally:
        F.save = orig
    return holder['fig']


def text_items(fig):
    out = []
    for ax in fig.axes:
        items = list(ax.texts) + [ax.title, ax.xaxis.label, ax.yaxis.label]
        if ax.axison:
            # деления вне текущих пределов оси не отрисовываются:
            # matplotlib оставляет их объекты, но на холст они не попадают
            lo_x, hi_x = sorted(ax.get_xlim())
            lo_y, hi_y = sorted(ax.get_ylim())
            for tk, lo, hi in ((ax.xaxis, lo_x, hi_x), (ax.yaxis, lo_y, hi_y)):
                for loc, lab in zip(tk.get_ticklocs(), tk.get_ticklabels()):
                    if lo - 1e-9 <= loc <= hi + 1e-9:
                        items.append(lab)
        lg = ax.get_legend()
        if lg:
            items += list(lg.get_texts())
        out += items
    out += list(fig.texts)
    res = []
    for t in out:
        if not t.get_text().strip() or not t.get_visible():
            continue
        res.append(t)
    return res


def bboxes(fig, items):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    res = []
    for t in items:
        try:
            bb = t.get_window_extent(renderer=r)
        except Exception:
            continue
        if bb.width > 0 and bb.height > 0:
            patch = t.get_bbox_patch()
            shielded = False
            if patch is not None:
                fc = patch.get_facecolor()
                shielded = len(fc) < 4 or fc[3] > 0.85
            res.append((t.get_text().replace('\n', ' / ')[:44], bb, shielded,
                        matplotlib.colors.to_rgb(t.get_color())))
    return res


def render(fig):
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    img = buf.reshape(h, w, 4)[:, :, 1:]      # ARGB -> RGB
    return img


def ink_mask(fig, items):
    """Изображение одних лишь данных, без подписей."""
    vis = [t.get_visible() for t in items]
    for t in items:
        t.set_visible(False)
    img = render(fig)
    for t, v in zip(items, vis):
        t.set_visible(v)
    return img


def overlap(b1, b2):
    dx = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
    dy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy / min(b1.width * b1.height, b2.width * b2.height)


def check(idx):
    fig = capture(idx)
    items = text_items(fig)
    boxes = bboxes(fig, items)
    base = ink_mask(fig, items)
    H, W = base.shape[:2]
    problems = []

    # 1) текст на текст (подложка от этого не спасает)
    for a in range(len(boxes)):
        for b in range(a + 1, len(boxes)):
            if boxes[a][0] == boxes[b][0]:
                continue
            o = overlap(boxes[a][1], boxes[b][1])
            if o > TEXT_ON_TEXT:
                problems.append((o, 'текст/текст',
                                 f'«{boxes[a][0]}» × «{boxes[b][0]}»'))

    # 2) текст на данные.
    # Подпись внутри ровно закрашенного столбца читается нормально, поэтому
    # дефектом считается не заливка как таковая, а НЕОДНОРОДНЫЙ фон под
    # текстом: пересекающие его линии, границы, сетка, кромки секторов.
    for name, bb, shielded, tcol in boxes:
        if shielded:      # подпись на собственной непрозрачной подложке — читается
            continue
        x0 = max(int(bb.x0) + 1, 0); x1 = min(int(bb.x1) - 1, W - 1)
        y0 = max(int(H - bb.y1) + 1, 0); y1 = min(int(H - bb.y0) - 1, H - 1)
        if x1 <= x0 or y1 <= y0:
            continue
        patch = base[y0:y1, x0:x1].reshape(-1, 3)
        if patch.size == 0:
            continue
        cols, counts = np.unique(patch, axis=0, return_counts=True)
        bg = cols[counts.argmax()]
        busy = (np.abs(patch.astype(np.int16) - bg.astype(np.int16)).max(axis=1) > 40).mean()
        if busy > BUSY_LIMIT:
            problems.append((busy, 'текст/данные', f'«{name}»'))
            continue
        # подпись на цветной заливке допустима, если контраст достаточен
        # (например, белая подпись внутри тёмного столбца). Дефект — когда
        # яркости текста и подложки сближаются и текст «тонет».
        if np.abs(bg.astype(np.int16) - 255).max() > 12:
            lum_bg = float(np.dot(bg, (0.299, 0.587, 0.114)))
            lum_tx = float(np.dot(np.array(tcol) * 255, (0.299, 0.587, 0.114)))
            contrast = abs(lum_bg - lum_tx)
            if contrast < 90:
                problems.append((1 - contrast / 255, 'низкий контраст', f'«{name}»'))

    plt.close(fig)
    return problems


def main():
    total = 0
    for i in range(1, 19):
        pr = check(i)
        if pr:
            total += len(pr)
            print(f'--- Рисунок {i}: {len(pr)}')
            for v, kind, what in sorted(pr, reverse=True)[:8]:
                print(f'    {v:.2f}  {kind:13s} {what}')
    print('ИТОГО дефектов:', total)
    return total


if __name__ == '__main__':
    main()
