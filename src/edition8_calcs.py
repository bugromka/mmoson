# -*- coding: utf-8 -*-
"""
ММОСО'Н — редакция 8. Расчёты новых областей.

Области:
  A. Генетика замкнутой популяции (инбридинг, основатели, правила подбора пар)
  B. Сельское хозяйство: пересмотр и оптимизация
  C. Промышленность, добыча, переработка, отходы производства
  D. Стыковочный модуль: концепция
  E. Кошки в экосистеме
  F. Насекомые: опылители, разлагатели, кормовая база
  G. Города: реальные и виртуальные (Minecraft)

Величины, помеченные [П], взяты из действующей публикации (редакция 7
с разделами 20–27) и не пересчитываются. Остальное выводится из них.
"""
import json
import math
import os

import numpy as np
from scipy.optimize import linprog

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'edition8_results.json')

# ═════════════════════════════════════════════════════════════
# Исходные величины публикации  [П]
# ═════════════════════════════════════════════════════════════
R_CYL = 5000.0            # м, радиус цилиндра [П п.2.1]
L_CYL = 40.0              # км, цилиндрическая часть [П]
CAP_DEPTH = 4.5           # км, глубина полусферического торца [П]
L_TOT = L_CYL + 2 * CAP_DEPTH          # 49 км [П]
D_AXIS = 21.0             # км, межосевое расстояние [П]

N_CYL = 2                 # цилиндров [П]
N_PER_CYL = 500_000       # население одного цилиндра [П п.11.4]
N_TOT = 1_000_000         # [П]
N_LO, N_HI = 600_000, 1_200_000        # [П п.11.4]
BIRTH_RATE = 2.1          # [П п.11.4]

# обитаемая площадь: 1256,6 км² на цилиндр (цилиндрическая поверхность
# 2πR·L), торцы 293,4 км² — технические зоны [П §20]
AREA_CYL = 1256.6         # км² [П]
AREA_TOT = AREA_CYL * N_CYL           # 2513,2 км²

FARM_TOT = 1508.0         # км², всего сельхозугодий [П табл.5.5]
FARM_AGRI = 972.0         # км² [П]
CROPS = 807.0             # км², посевные площади [П табл.5.4]
RESERVE_FAST = 150.0      # км² [П]
FISH_POOLS = 15.0         # км² [П]

KCAL_DAY = 2800           # ккал/сут [П табл.5.1]
PROT_DAY = 70.0           # г/сут [П табл.5.1]
CAL_NEED = 1.022e12       # ккал/год [П табл.5.2]
PROT_NEED = 25_600.0      # т/год [П табл.5.2]
CAL_PROD = 1.870e12       # ккал/год [П табл.5.2]
PROT_PROD = 69_800.0      # т/год [П табл.5.2]

M_STATION = 46.70e9       # т [П п.4.3]
M_STEEL = 22.05e9         # т [П п.4.3]
P_OSB = 503.0             # ГВт [П табл.4.15]
P_TOT = 721.4             # ГВт [П табл.4.15]

WASTE_KG_DAY = 1.5        # кг/сут на человека [П п.11.2]
SEWAGE_L_DAY = 200.0      # л/сут на человека [П п.11.2]
WASTE_TOT = N_TOT * WASTE_KG_DAY * 365 / 1e3        # т/год = 547 500
SEWAGE_TOT = N_TOT * SEWAGE_L_DAY * 365 / 1e3       # м³/год = 73 000 000

# коррозия [П п.14.3, п.16.3]
CORR_OPEN = 0.01          # мм/год без покрытия [П]
CORR_COATED = 0.001       # мм/год с лакокрасочным покрытием [П]
OPEN_METAL_SHARE = 0.05   # доля открытого металла [П п.16.3]
OPEN_METAL_AREA = 155.0   # км² [П п.16.3]
STEEL_RHO = 7850.0        # кг/м³
STEEL_OXIDISED = 12.17e6  # т/год при 5 % открытого металла [П п.16.3]
O2_BOUND = 5.23e6         # т/год [П п.16.3]
O2_RESERVE = 1.58e9       # т запас кислорода [П п.16.4]

BEES_PER_CYL = 2000       # пчелосемей [П табл.5.3]
RING_D = 400.0            # м, подшипниковое кольцо [П]
N_STRUT = 24              # радиальных элемента [П]
V_SHELL = 221.5           # м/с, окружная скорость обшивки [П]

# астероид-источник [П прил.Г]
AST_M_DIAM = 3000.0       # м, (6178) 1986 DA
AST_M_RHO = 5000.0        # кг/м³, металлический тип

RES = {}

# ═════════════════════════════════════════════════════════════
# A. ГЕНЕТИКА ЗАМКНУТОЙ ПОПУЛЯЦИИ
# ═════════════════════════════════════════════════════════════
T_GEN = 28.0                       # лет, средний возраст родителей
HORIZON = 200.0                    # лет, срок службы [П]
G = HORIZON / T_GEN

VK = 3.0                           # дисперсия числа потомков (>2 по Пуассону)
NE_TOT = (4 * N_TOT - 2) / (VK + 2)
NE_CYL = NE_TOT / N_CYL
DF_GEN = 1.0 / (2 * NE_TOT)
F_HORIZON = 1.0 - (1.0 - DF_GEN) ** G

NE_500 = 500.0                     # правило 50/500 (Franklin 1980)
DF_500 = 1.0 / (2 * NE_500)
F_500_H = 1.0 - (1.0 - DF_500) ** G

DF_TARGET = 0.001                  # 0,1 % за поколение
NE_REQ = 1.0 / (2 * DF_TARGET)
FOUNDER_MIN = 5000
DF_FOUNDER = 1.0 / (2 * FOUNDER_MIN)
F_FOUNDER_H = 1.0 - (1.0 - DF_FOUNDER) ** G

F_CONSANG = {
    'полные сибсы': 0.125,
    'полусибсы': 0.0625,
    'дяди–племянники': 0.125,
    'двоюродные сибсы': 0.0625,
    'двоюродные один раз в колене': 0.03125,
    'троюродные сибсы': 0.015625,
    'четвероюродные сибсы': 0.00390625,
}
F_1ST = F_CONSANG['двоюродные сибсы']
F_2ND = F_CONSANG['троюродные сибсы']
F_ALLOWED_GEN = 0.0001             # 0,01 % в средний F поколения
SHARE_2ND = F_ALLOWED_GEN / F_2ND
SHARE_1ST = F_ALLOWED_GEN / F_1ST

# два цилиндра: островная модель F_ST ≈ 1/(4·N_e·m + 1)
MIG_TEST = 0.01
FST_TEST = 1.0 / (4 * NE_CYL * MIG_TEST + 1)
MIG_FST_001 = 99.0 / (4 * NE_CYL)
MIG_FST_0001 = 999.0 / (4 * NE_CYL)
# минимальный обмен, при котором цилиндры остаются одной популяцией
# (F_ST < 0,01 — порог заметной дифференциации)
MIG_MIN = MIG_FST_001

LE = 1.5                           # летальных эквивалента на человека
LE_F001 = LE * 0.01
LE_F01 = LE * 0.10

DONORS = 10_000
DONOR_NE = DONORS / 2
DONOR_DF = 1.0 / (2 * DONOR_NE)

# кровнородственное требование: F максимально допустимого брака
F_MAX_MARRIAGE = F_2ND            # троюродные сибсы

RES['A_genetics'] = dict(
    T_gen=T_GEN, horizon=HORIZON, generations=G,
    N_tot=N_TOT, N_per_cyl=N_PER_CYL, Vk=VK,
    Ne_tot=NE_TOT, Ne_cyl=NE_CYL, dF_gen=DF_GEN, F_horizon=F_HORIZON,
    Ne_500=NE_500, dF_500=DF_500, F_500_horizon=F_500_H,
    Ne_required=NE_REQ, dF_target=DF_TARGET,
    founder_min=FOUNDER_MIN, dF_founder=DF_FOUNDER,
    F_founder_horizon=F_FOUNDER_H,
    F_consang=F_CONSANG, F_first_cousin=F_1ST, F_second_cousin=F_2ND,
    F_allowed_gen=F_ALLOWED_GEN, share_second_cousin=SHARE_2ND,
    share_first_cousin=SHARE_1ST,
    migration_test=MIG_TEST, F_ST_at_test=FST_TEST,
    migration_for_FST_001=MIG_FST_001, migration_for_FST_0001=MIG_FST_0001,
    migration_min=MIG_MIN,
    lethal_equivalents=LE, LE_at_F_001=LE_F001, LE_at_F_01=LE_F01,
    donors=DONORS, donor_Ne=DONOR_NE, donor_dF=DONOR_DF,
    F_max_marriage=F_MAX_MARRIAGE,
    people_per_generation=N_TOT / G,
)

# ═════════════════════════════════════════════════════════════
# B. СЕЛЬСКОЕ ХОЗЯЙСТВО
# ═════════════════════════════════════════════════════════════
# Действующая структура посевов [П табл.5.4] с уточнением состава по массе
# (свежая vs сухая) — от этого зависит пересчёт в белок.
# культура, км², кг/м²·год (свежая масса), ккал/кг, доля белка (в этой массе)
CROPS_TAB = [
    ('Рис',                 120.0, 1.00, 3600, 0.075),
    ('Кукуруза',            150.0, 1.20, 3650, 0.090),
    ('Пшеница',              50.0, 1.00, 3400, 0.110),
    ('Ячмень',               20.0, 1.00, 3520, 0.100),
    ('Картофель',           100.0, 4.00,  770, 0.020),
    ('Батат, таро, маниок',  46.0, 3.00,  900, 0.015),
    ('Соя',                  10.0, 0.35, 4460, 0.360),
    ('Прочие бобовые',       36.0, 0.30, 3500, 0.220),
    ('Овощи',                80.0, 4.00,  250, 0.015),
    ('Фрукты и ягоды',       60.0, 2.00,  500, 0.008),
    ('Масличные',            50.0, 0.50, 6000, 0.200),
    ('Грибы',                30.0, 10.0,  250, 0.031),
    ('Зелень и пряности',    25.0, 3.00,  200, 0.025),
    ('Водоросли',            30.0, 2.00,  350, 0.015),
]

rows = []
for name, km2, yld, kcal_kg, prot_frac in CROPS_TAB:
    area = km2 * 1e6
    prod_t = yld * area / 1e3
    kcal = prod_t * 1e3 * kcal_kg
    prot_t = prod_t * prot_frac
    rows.append(dict(name=name, km2=km2, yld=yld, kcal_kg=kcal_kg,
                     prot_frac=prot_frac, prod_t=prod_t, kcal=kcal,
                     prot_t=prot_t,
                     kcal_m2=kcal / area, prot_g_m2=prot_t * 1e6 / area))

AREA_SUM = sum(r['km2'] for r in rows)
KCAL_SUM = sum(r['kcal'] for r in rows)
CAL_GROSS = KCAL_SUM                    # валовая продукция таблицы 5.4
CAL_NET_GAP = CAL_GROSS - CAL_PROD      # необъяснённый перепад
CAL_NET_GAP_SHARE = CAL_NET_GAP / CAL_GROSS
PROT_SUM = sum(r['prot_t'] for r in rows)

ANIMAL = [('Рыба', 70_000.0, 0.18), ('Молоко', 33_750.0, 0.033),
          ('Мясо наземных', 8_000.0, 0.20), ('Яйца', 5_000.0, 0.125),
          ('Мёд', 60.0, 0.004)]
ANIMAL_PROT = sum(v * f for _, v, f in ANIMAL)

PROT_TOTAL = PROT_SUM + ANIMAL_PROT
PROT_ANIMAL_SHARE = ANIMAL_PROT / PROT_TOTAL
KCAL_M2_AVG = KCAL_SUM / (AREA_SUM * 1e6)
PROT_G_M2_AVG = PROT_TOTAL * 1e6 / (AREA_SUM * 1e6)

# ── оптимизация посевов: минимум площади при тех же калориях и белке ──
# ограничения: калории и белок не ниже действующих; каждая культура
# сохраняет не менее 20 % своей площади (разнообразие, вредители, почва);
# расширение не более чем втрое (риск монокультуры)
n = len(rows)
c = np.array([r['km2'] for r in rows], dtype=float)          # минимизируем сумму
# площади в км²; отдача в ккал/м² и г/м²; перевод км²→м² даёт множитель 1e6
A_ub = np.vstack([-np.array([r['kcal_m2'] for r in rows]),
                  -np.array([r['prot_g_m2'] for r in rows])])
b_ub = np.array([-CAL_GROSS / 1e6, -PROT_PROD * 1e6 / 1e6])
bounds = [(r['km2'] * 0.20, r['km2'] * 3.0) for r in rows]
res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
assert res.success, res.message
AREA_OPT = float(res.x.sum())
KCAL_OPT = float(np.dot(res.x, [r['kcal_m2'] for r in rows]) * 1e6)
PROT_OPT = float(np.dot(res.x, [r['prot_g_m2'] for r in rows]) * 1e6 / 1e6)
AREA_FREED = AREA_SUM - AREA_OPT
KCAL_M2_OPT = KCAL_OPT / (AREA_OPT * 1e6)

# ── сценарий 2: рациональный запас вместо действующего ──
# действующий запас: калории ×1,83, белок ×2,73 — несоразно белковый.
# принимается запас калориям 15 %, белку 20 %.
CAL_MARGIN, PROT_MARGIN = 1.15, 1.20
b_ub2 = np.array([-CAL_NEED * CAL_MARGIN / 1e6, -PROT_NEED * PROT_MARGIN * 1e6 / 1e6])
res2 = linprog(c, A_ub=A_ub, b_ub=b_ub2, bounds=bounds, method='highs')
assert res2.success, res2.message
AREA_OPT2 = float(res2.x.sum())
KCAL_OPT2 = float(np.dot(res2.x, [r['kcal_m2'] for r in rows]) * 1e6)
PROT_OPT2 = float(np.dot(res2.x, [r['prot_g_m2'] for r in rows]) * 1e6 / 1e6)
AREA_FREED2 = AREA_SUM - AREA_OPT2
KCAL_M2_OPT2 = KCAL_OPT2 / (AREA_OPT2 * 1e6)

# оптимизация по одному калорийному признаку — теоретический предел
BEST_KCAL_M2 = max(r['kcal_m2'] for r in rows)
AREA_THEOR = CAL_PROD / (BEST_KCAL_M2 * 1e6)
BEST_PROT_M2 = max(r['prot_g_m2'] for r in rows)
AREA_THEOR_P = PROT_PROD * 1e6 / BEST_PROT_M2 / 1e6

# ── многоярусное выращивание в холодной зоне ──
# холодная зона 32–40 км [П §3.4]; в открытом грунте там только
# морозостойкие многолетники. Сценарии перевода части зоны на ярусное
# выращивание зелени.
COLD_KM = 8.0                                   # длина холодной зоны [П §3.4]
COLD_AREA = COLD_KM * (2 * math.pi * R_CYL / 1e3)   # км²
GREEN_KCAL_KG = 200.0                           # ккал/кг зелени
GREEN_YIELD_LAYER = 6.0                         # кг/м²·год на ярус
GREEN_YIELD_OPEN = 1.0                          # кг/м²·год в открытом грунте
COLD_SCEN = []
for share in (0.10, 0.20, 0.30):
    for layers in (3, 4):
        area = COLD_AREA * share
        gain_t = area * 1e6 * (layers * GREEN_YIELD_LAYER - GREEN_YIELD_OPEN) / 1e3
        COLD_SCEN.append(dict(share=share, layers=layers, area=area,
                              gain_t=gain_t,
                              kcal_tln=gain_t * 1e3 * GREEN_KCAL_KG / 1e12,
                              share_of_need=gain_t * 1e3 * GREEN_KCAL_KG / CAL_NEED))
COLD_BASE = COLD_SCEN[1]                        # 20 % зоны, 3 яруса

# ── резерв быстрых культур ──
FAST_CYCLE = 20            # суток, редис/салат/шпинат
FAST_YIELD = 3.0           # кг/м² за цикл
FAST_CYCLES_YR = 365 / FAST_CYCLE
RESERVE_REDUCED = RESERVE_FAST * 0.60   # 6 % угодий вместо 10 %

RES['B_agriculture'] = dict(
    area_current=AREA_SUM, kcal_current=KCAL_SUM, prot_current=PROT_SUM,
    kcal_need=CAL_NEED, prot_need=PROT_NEED,
    kcal_prod=CAL_PROD, prot_prod=PROT_PROD,
    animal_prot=ANIMAL_PROT, prot_total=PROT_TOTAL,
    prot_animal_share=PROT_ANIMAL_SHARE,
    kcal_m2_avg=KCAL_M2_AVG, prot_g_m2_avg=PROT_G_M2_AVG,
    area_optimised=AREA_OPT, kcal_optimised=KCAL_OPT, prot_optimised=PROT_OPT,
    area_freed=AREA_FREED, area_freed_share=AREA_FREED / AREA_SUM,
    kcal_m2_optimised=KCAL_M2_OPT,
    cal_margin=CAL_MARGIN, prot_margin=PROT_MARGIN,
    area_optimised2=AREA_OPT2, kcal_optimised2=KCAL_OPT2, prot_optimised2=PROT_OPT2,
    area_freed2=AREA_FREED2, area_freed2_share=AREA_FREED2 / AREA_SUM,
    kcal_m2_optimised2=KCAL_M2_OPT2,
    surplus_cal=CAL_PROD / CAL_NEED, surplus_prot=PROT_PROD / PROT_NEED,
    best_kcal_m2=BEST_KCAL_M2, best_prot_m2=BEST_PROT_M2,
    area_theoretical=AREA_THEOR, area_theoretical_protein=AREA_THEOR_P,
    optimised_mix={r['name']: round(float(x), 2)
                   for r, x in zip(rows, res.x)},
    cold_area=COLD_AREA, cold_scen=COLD_SCEN, cold_base=COLD_BASE,
    green_yield_layer=GREEN_YIELD_LAYER, green_yield_open=GREEN_YIELD_OPEN,
    green_kcal_kg=GREEN_KCAL_KG,
    cal_gross=CAL_GROSS, cal_net_gap=CAL_NET_GAP,
    cal_net_gap_share=CAL_NET_GAP_SHARE,
    reserve_current=RESERVE_FAST, reserve_reduced=RESERVE_REDUCED,
    fast_cycle=FAST_CYCLE, fast_yield=FAST_YIELD,
    cal_rank=sorted([(r['name'], r['kcal_m2']) for r in rows],
                    key=lambda t: -t[1])[:5],
    prot_rank=sorted([(r['name'], r['prot_g_m2']) for r in rows],
                     key=lambda t: -t[1])[:5],
    farm_total=FARM_TOT, farm_agri=FARM_AGRI, crops=CROPS,
    farm_after=FARM_AGRI - AREA_FREED,
)

# ═════════════════════════════════════════════════════════════
# C. ПРОМЫШЛЕННОСТЬ, ДОБЫЧА, ПЕРЕРАБОТКА, ОТХОДЫ
# ═════════════════════════════════════════════════════════════
WASTE_ORG = WASTE_TOT * 0.60
WASTE_METGLASS = WASTE_TOT * 0.25
WASTE_REST = WASTE_TOT * 0.15

MET_SHARE, GLASS_SHARE = 0.55, 0.45
REC_MET, REC_GLASS = 0.95, 0.85
MET_REC = WASTE_METGLASS * MET_SHARE * REC_MET
GLASS_REC = WASTE_METGLASS * GLASS_SHARE * REC_GLASS
REST_LOST = WASTE_METGLASS - MET_REC - GLASS_REC

COMPOST_T = WASTE_ORG * 0.55
BSF_FEED = WASTE_ORG * 0.35
BIOGAS = WASTE_ORG * 0.10

CLOSED = COMPOST_T + MET_REC + GLASS_REC + BSF_FEED
OPENED = WASTE_TOT - CLOSED
CLOSURE = CLOSED / WASTE_TOT

# коррозионный контур [П п.16.3]
STEEL_NEED_OPEN = STEEL_OXIDISED
STEEL_NEED_COATED = STEEL_OXIDISED * (CORR_COATED / CORR_OPEN)
STEEL_200Y_OPEN = STEEL_NEED_OPEN * 200
STEEL_200Y_COATED = STEEL_NEED_COATED * 200

# астероидный источник
AST_VOL = 4 / 3 * math.pi * (AST_M_DIAM / 2) ** 3
AST_MASS_KG = AST_VOL * AST_M_RHO
AST_MASS_T = AST_MASS_KG / 1e3
AST_COVERS = AST_MASS_T / (M_STEEL + STEEL_200Y_COATED)

# энергия плавки: 20 ГДж/т от руды (электросталь ~2,5 ГДж/т)
SMELT_GJ_T = 20.0
SMELT_POWER = STEEL_NEED_COATED * SMELT_GJ_T / (365 * 24 * 3600)   # ГВт

RES['C_industry'] = dict(
    waste_total=WASTE_TOT, waste_org=WASTE_ORG,
    waste_metglass=WASTE_METGLASS, waste_rest=WASTE_REST,
    sewage=SEWAGE_TOT,
    met_recovered=MET_REC, glass_recovered=GLASS_REC, rest_lost=REST_LOST,
    compost=COMPOST_T, bsf_feed=BSF_FEED, biogas=BIOGAS,
    closed=CLOSED, opened=OPENED, closure=CLOSURE,
    corr_open=CORR_OPEN, corr_coated=CORR_COATED,
    open_metal_share=OPEN_METAL_SHARE, open_metal_area=OPEN_METAL_AREA,
    steel_oxidised=STEEL_OXIDISED, o2_bound=O2_BOUND, o2_reserve=O2_RESERVE,
    steel_need_open=STEEL_NEED_OPEN, steel_need_coated=STEEL_NEED_COATED,
    steel_200y_open=STEEL_200Y_OPEN, steel_200y_coated=STEEL_200Y_COATED,
    ast_diam=AST_M_DIAM, ast_rho=AST_M_RHO, ast_vol=AST_VOL, ast_mass_kg=AST_MASS_KG, ast_mass_t=AST_MASS_T,
    ast_covers=AST_COVERS, m_station=M_STATION, m_steel=M_STEEL,
    smelt_gj_t=SMELT_GJ_T, smelt_power_GW=SMELT_POWER,
    p_total=P_TOT, smelt_share=SMELT_POWER / P_TOT,
)

# ═════════════════════════════════════════════════════════════
# D. СТЫКОВОЧНЫЙ МОДУЛЬ
# ═════════════════════════════════════════════════════════════
RING_R = RING_D / 2
RING_AREA = math.pi * RING_R ** 2
RING_CIRC = 2 * math.pi * RING_R
STRUT_SECTION = 2.5     # м² на элемент (коробчатый профиль, оценка)
STRUT_AREA_TOT = N_STRUT * STRUT_SECTION

SETTLE_DAYS = 7.7
QUAR_DAYS = 40
SETTLE_RATE = N_PER_CYL / SETTLE_DAYS
QUAR_PLACES = N_PER_CYL * QUAR_DAYS / SETTLE_DAYS

DOCK_MASS = 12_000.0
AIRLOCKS = 3
AIRLOCK_VOL = 850.0
AIRLOCK_TOT = AIRLOCKS * AIRLOCK_VOL
AIR_MASS = AIRLOCK_TOT * 1.2
DOCK_ENERGY_GJ = 1.8

CARGO_YR = 1.5e6
CARGO_DAY = CARGO_YR / 365
V_SHELL_KMH = V_SHELL * 3.6

RES['D_docking'] = dict(
    ring_d=RING_D, ring_r=RING_R, ring_area=RING_AREA, ring_circ=RING_CIRC,
    n_strut=N_STRUT, strut_section=STRUT_SECTION, strut_area=STRUT_AREA_TOT,
    settle_days=SETTLE_DAYS, quar_days=QUAR_DAYS, settle_rate=SETTLE_RATE,
    quar_places=QUAR_PLACES,
    dock_mass=DOCK_MASS, airlocks=AIRLOCKS, airlock_vol=AIRLOCK_VOL,
    airlock_tot=AIRLOCK_TOT, air_mass=AIR_MASS,
    dock_energy_GJ=DOCK_ENERGY_GJ,
    cargo_yr=CARGO_YR, cargo_day=CARGO_DAY,
    v_shell=V_SHELL, v_shell_kmh=V_SHELL_KMH,
    l_tot=L_TOT, d_axis=D_AXIS,
)

# ═════════════════════════════════════════════════════════════
# E. КОШКИ В ЭКОСИСТЕМЕ
# ═════════════════════════════════════════════════════════════
GRAIN_T = (120_000 + 180_000 + 50_000 + 20_000) * 0.55   # т в хранилище
GRAIN_RHO = 0.75                                        # т/м³ насыпного
GRAIN_VOL = GRAIN_T / GRAIN_RHO
STACK_H = 6.0
STORE_AREA = GRAIN_VOL / STACK_H

CAT_PER_1000 = 6.0
CATS_TOT = N_TOT / 1000 * CAT_PER_1000
CATS_CYL = CATS_TOT / N_CYL

CAT_MASS = 4.0
CAT_KCAL_DAY = 60.0 * CAT_MASS ** 0.75      # ~170 ккал/сут
FOOD_KCAL_KG = 4000.0                       # ккал/кг корма
CAT_FOOD_T = CATS_TOT * CAT_KCAL_DAY * 365 / FOOD_KCAL_KG / 1e3
CAT_PROT_T = CAT_FOOD_T * 0.32
CAT_MEAT_SHARE = 0.65
CAT_MEAT_T = CAT_FOOD_T * CAT_MEAT_SHARE

FISH_WASTE_SHARE = 0.30
FISH_WASTE = 70_000 * FISH_WASTE_SHARE
BSF_MEAL_SHARE = 0.35
BSF_FOR_CATS = CAT_MEAT_T * BSF_MEAL_SHARE

CAT_PER_STORE_AREA = 1200.0                 # м² хранилища на кота
CATS_STORE = STORE_AREA / CAT_PER_STORE_AREA
CATS_PET = CATS_TOT - min(CATS_STORE, CATS_TOT)

TOXO_SHARE = 0.30

RES['E_cats'] = dict(
    grain_t=GRAIN_T, grain_rho=GRAIN_RHO, grain_vol=GRAIN_VOL,
    stack_h=STACK_H, store_area=STORE_AREA,
    cats_per_1000=CAT_PER_1000, cats_total=CATS_TOT, cats_per_cyl=CATS_CYL,
    cat_mass=CAT_MASS, cat_kcal_day=CAT_KCAL_DAY,
    food_kcal_kg=FOOD_KCAL_KG, cat_food_t=CAT_FOOD_T, cat_prot_t=CAT_PROT_T,
    cat_meat_share=CAT_MEAT_SHARE, cat_meat_t=CAT_MEAT_T,
    fish_waste=FISH_WASTE, bsf_meal_share=BSF_MEAL_SHARE,
    bsf_for_cats=BSF_FOR_CATS,
    cat_per_store_area=CAT_PER_STORE_AREA, cats_store=CATS_STORE,
    cats_pet=CATS_PET, toxo_share=TOXO_SHARE,
    cats_share_of_population=CATS_TOT / N_TOT,
)

# ═════════════════════════════════════════════════════════════
# F. НАСЕКОМЫЕ
# ═════════════════════════════════════════════════════════════
BEES_TOT = BEES_PER_CYL * N_CYL
HONEY_T = 60.0
HONEY_PER_COLONY_KG = HONEY_T * 1e3 / BEES_TOT

POLLINATED = 60.0 + 50.0 + 10.0 + 36.0
POLLINATED_SHARE = POLLINATED / CROPS

GREENHOUSE = 80.0
BUMBLE_PER_M2 = 1 / 250.0
BUMBLE_COLONIES = GREENHOUSE * 1e6 * BUMBLE_PER_M2

BSF_CONV = 0.20        # доля сырья в сухой личинке
BSF_PROT = 0.42        # доля белка в сухой личинке
BSF_LARVA = BSF_FEED * BSF_CONV
BSF_PROT_T = BSF_LARVA * BSF_PROT
BSF_LEFT = BSF_LARVA - BSF_FOR_CATS

FISH_FEED = 70_000 * 1.8      # т/год, FCR 1,8
CHICK_FEED = 5_000 * 2.2      # т/год, FCR 2,2
FEED_FROM_BSF = min(BSF_LEFT, FISH_FEED * 0.30 + CHICK_FEED * 0.30)
FEED_SHORTFALL = (FISH_FEED * 0.30 + CHICK_FEED * 0.30) - FEED_FROM_BSF

RES['F_insects'] = dict(
    bees_total=BEES_TOT, honey_t=HONEY_T, honey_per_colony_kg=HONEY_PER_COLONY_KG,
    pollinated=POLLINATED, pollinated_share=POLLINATED_SHARE,
    greenhouse=GREENHOUSE, bumble_colonies=BUMBLE_COLONIES,
    bsf_feed=BSF_FEED, bsf_conv=BSF_CONV, bsf_prot=BSF_PROT,
    bsf_larva=BSF_LARVA, bsf_prot_t=BSF_PROT_T,
    bsf_for_cats=BSF_FOR_CATS, bsf_left=BSF_LEFT,
    fish_feed=FISH_FEED, chick_feed=CHICK_FEED,
    feed_from_bsf=FEED_FROM_BSF, feed_shortfall=FEED_SHORTFALL,
    bsf_feed_per_year_t=BSF_FEED,
)

# ═════════════════════════════════════════════════════════════
# G. ГОРОДА: РЕАЛЬНЫЕ И ВИРТУАЛЬНЫЕ
# ═════════════════════════════════════════════════════════════
DENSITY = N_TOT / AREA_TOT                  # человек/км²
URBAN_M2 = 120.0
URBAN_AREA = N_TOT * URBAN_M2 / 1e6
URBAN_SHARE = URBAN_AREA / AREA_TOT
PARK_M2 = 25.0
PARK_AREA = N_TOT * PARK_M2 / 1e6

CITY_POP = 50_000
CITY_AREA = CITY_POP * URBAN_M2 / 1e6
N_CITIES = N_TOT / CITY_POP
CITY_RADIUS = math.sqrt(CITY_AREA / math.pi)

MC_WORLD = 29_999_984
MC_HEIGHT = 320
CYL_LEN_M = L_TOT * 1e3
CYL_DIA_M = 2 * R_CYL

mc = {}
for sc in (1, 100, 200, 1000, 2000):
    bl = CYL_LEN_M / sc
    bd = CYL_DIA_M / sc
    mc[sc] = dict(blocks_len=bl, blocks_dia=bd, surface=bl * bd,
                  fits=(bl <= MC_WORLD and bd <= MC_WORLD))
# 1:1 возможен только при горизонтальной укладке (диаметр в плане)
mc[1]['fits_height'] = CYL_DIA_M <= MC_HEIGHT

MC_REC = 100
MC_REC_LEN = CYL_LEN_M / MC_REC
MC_REC_DIA = CYL_DIA_M / MC_REC
MC_REC_SURFACE = MC_REC_LEN * MC_REC_DIA

MC_DISTRICT_M = 1000.0
MC_DISTRICT_SCALE = 100
MC_DISTRICT_BLOCKS = MC_DISTRICT_M / MC_DISTRICT_SCALE

MC_1TO1_SURFACE = CYL_LEN_M * CYL_DIA_M

RES['G_cities'] = dict(
    area_cyl=AREA_CYL, area_tot=AREA_TOT, density=DENSITY,
    urban_m2=URBAN_M2, urban_area=URBAN_AREA, urban_share=URBAN_SHARE,
    park_m2=PARK_M2, park_area=PARK_AREA,
    city_pop=CITY_POP, city_area=CITY_AREA, n_cities=N_CITIES,
    city_radius=CITY_RADIUS,
    mc_world=MC_WORLD, mc_height=MC_HEIGHT,
    mc=mc, mc_recommended=MC_REC,
    mc_rec_len=MC_REC_LEN, mc_rec_dia=MC_REC_DIA,
    mc_rec_surface=MC_REC_SURFACE,
    mc_district_blocks=MC_DISTRICT_BLOCKS,
    mc_district_scale=MC_DISTRICT_SCALE,
    mc_1to1_surface=MC_1TO1_SURFACE,
    cyl_len_m=CYL_LEN_M, cyl_dia_m=CYL_DIA_M,
)


# ═════════════════════════════════════════════════════════════
# Отчёт
# ═════════════════════════════════════════════════════════════
if __name__ == '__main__':
    A = RES['A_genetics']
    print('=' * 74)
    print('A. ГЕНЕТИКА ЗАМКНУТОЙ ПОПУЛЯЦИИ')
    print('=' * 74)
    print(f"  Население {A['N_tot']:,} ({A['N_per_cyl']:,} на цилиндр)")
    print(f"  Поколение {A['T_gen']:.0f} лет; горизонт {A['horizon']:.0f} лет = "
          f"{A['generations']:.2f} поколений")
    print(f"  N_e = {A['Ne_tot']:,.0f} (Vk={A['Vk']}); ΔF = {A['dF_gen']:.2e} за поколение; "
          f"F за 200 лет = {A['F_horizon']*100:.5f} %")
    print(f"  Правило 50/500: N_e=500 → ΔF={A['dF_500']:.1e}, "
          f"F за 200 лет = {A['F_500_horizon']*100:.3f} %")
    print(f"  Порог ΔF ≤ 0,1 %/поколение → N_e ≥ {A['Ne_required']:,.0f}")
    print(f"  Основатели {A['founder_min']:,} → ΔF={A['dF_founder']:.1e}, "
          f"F за 200 лет = {A['F_founder_horizon']*100:.4f} %")
    print(f"  Кровное родство: двоюродные {A['F_first_cousin']*100:.2f} %, "
          f"троюродные {A['F_second_cousin']*100:.4f} %")
    print(f"  При вкладе {A['F_allowed_gen']*100:.3f} %/поколение: троюродные до "
          f"{A['share_second_cousin']*100:.2f} % браков, двоюродные до "
          f"{A['share_first_cousin']*100:.3f} %")
    print(f"  Два цилиндра: обмен {A['migration_test']*100:.0f} % родителей → "
          f"F_ST = {A['F_ST_at_test']:.2e}")
    print(f"  Для F_ST = 0,01 нужен обмен {A['migration_for_FST_001']*100:.4f} %; "
          f"для F_ST = 0,001 — {A['migration_for_FST_0001']*100:.4f} %")
    print(f"  Генетический груз: {A['lethal_equivalents']} летальных эквивалента; при F=1 % "
          f"+{A['LE_at_F_001']:.3f}, при F=10 % +{A['LE_at_F_01']:.2f}")
    print(f"  Банк гамет: {A['donors']:,} доноров → N_e={A['donor_Ne']:,.0f}, "
          f"ΔF={A['donor_dF']:.1e}")

    B = RES['B_agriculture']
    print()
    print('=' * 74)
    print('B. СЕЛЬСКОЕ ХОЗЯЙСТВО')
    print('=' * 74)
    print(f"  Действующая структура: {B['area_current']:.0f} км² → "
          f"{B['kcal_current']/1e12:.2f} трлн ккал, {B['prot_current']:,.0f} т белка")
    print(f"  Публикация: {B['kcal_prod']/1e12:.2f} трлн ккал, "
          f"{B['prot_prod']:,.0f} т белка (расхождение уточняется)")
    print(f"  Потребность: {B['kcal_need']/1e12:.3f} трлн ккал, "
          f"{B['prot_need']:,.0f} т белка")
    print(f"  Средняя отдача: {B['kcal_m2_avg']:.0f} ккал/м², "
          f"{B['prot_g_m2_avg']:.1f} г белка/м²")
    print(f"  Животноводство: {B['animal_prot']:,.0f} т белка "
          f"({B['prot_animal_share']*100:.1f} %)")
    print(f"  Оптимизировано: {B['area_optimised']:.0f} км² → "
          f"{B['kcal_optimised']/1e12:.2f} трлн ккал, {B['prot_optimised']:,.0f} т белка")
    print(f"  Высвобождение {B['area_freed']:.0f} км² "
          f"({B['area_freed_share']*100:.1f} % посевов); "
          f"отдача выросла до {B['kcal_m2_optimised']:.0f} ккал/м²")
    print(f"  Действующий запас: калории ×{B['surplus_cal']:.2f}, "
          f"белок ×{B['surplus_prot']:.2f} — белковый запас несоразен")
    print(f"  Сценарий 2 (запас ×{B['cal_margin']:.2f} по калориям, "
          f"×{B['prot_margin']:.2f} по белку): {B['area_optimised2']:.0f} км² → "
          f"{B['kcal_optimised2']/1e12:.2f} трлн ккал, "
          f"{B['prot_optimised2']:,.0f} т белка".replace(',', ' '))
    print(f"    высвобождение {B['area_freed2']:.0f} км² "
          f"({B['area_freed2_share']*100:.1f} % посевов), отдача "
          f"{B['kcal_m2_optimised2']:.0f} ккал/м²")
    print(f"  Теоретический предел: {B['area_theoretical']:.0f} км² "
          f"(по калориям), {B['area_theoretical_protein']:.0f} км² (по белку)")
    print('  Калорийность, ккал/м²:', ', '.join(f'{n} {v:.0f}' for n, v in B['cal_rank']))
    print('  Белок, г/м²:', ', '.join(f'{n} {v:.0f}' for n, v in B['prot_rank']))
    print(f"  Несостыковка документа: валовая продукция посевов "
          f"{B['cal_gross']/1e12:.2f} трлн ккал против нетто "
          f"{B['kcal_prod']/1e12:.2f} трлн ккал — перепад "
          f"{B['cal_net_gap']/1e12:.2f} трлн ккал "
          f"({B['cal_net_gap_share']*100:.1f} %) не объяснён")
    print(f"  Холодная зона {B['cold_area']:.1f} км², сценарии ярусного выращивания:")
    for sc in B['cold_scen']:
        print(f"    {sc['share']*100:.0f} % зоны, {sc['layers']} ярусов: "
              f"+{sc['gain_t']/1e3:.0f} тыс. т зелени, "
              f"{sc['kcal_tln']:.2f} трлн ккал "
              f"({sc['share_of_need']*100:.1f} % потребности)")
    print(f"  Резерв быстрых культур: {B['reserve_current']:.0f} → "
          f"{B['reserve_reduced']:.0f} км²")
    print(f"  Сельхозугодия после оптимизации: {B['farm_after']:.0f} км² "
          f"из {B['farm_total']:.0f} км²")

    C = RES['C_industry']
    print()
    print('=' * 74)
    print('C. ПРОМЫШЛЕННОСТЬ И ОТХОДЫ')
    print('=' * 74)
    print(f"  Твёрдые отходы {C['waste_total']/1e6:.3f} млн т/год: органика "
          f"{C['waste_org']/1e6:.3f}, металл+стекло {C['waste_metglass']/1e6:.3f}, "
          f"остаток {C['waste_rest']/1e6:.3f}")
    print(f"  Стоки {C['sewage']/1e6:.1f} млн м³/год")
    print(f"  Коррозия: {C['corr_open']} мм/год без покрытия, "
          f"{C['corr_coated']} мм/год с покрытием")
    print(f"  При {C['open_metal_share']*100:.0f} % открытого металла "
          f"({C['open_metal_area']:.0f} км²): окисляется "
          f"{C['steel_oxidised']/1e6:.2f} млн т стали/год, связывая "
          f"{C['o2_bound']/1e6:.2f} млн т O₂/год")
    print(f"  С покрытиями: {C['steel_need_coated']/1e6:.2f} млн т/год; "
          f"за 200 лет {C['steel_200y_coated']/1e6:.0f} млн т")
    print(f"  Без покрытий: за 200 лет {C['steel_200y_open']/1e6:.0f} млн т")
    print(f"  Возврат из бытовых отходов: металл {C['met_recovered']/1e3:.0f} тыс. т, "
          f"стекло {C['glass_recovered']/1e3:.0f} тыс. т, компост "
          f"{C['compost']/1e3:.0f} тыс. т, корм {C['bsf_feed']/1e3:.0f} тыс. т")
    print(f"  Замыкание бытового контура: {C['closure']*100:.1f} %; "
          f"незамкнутый остаток {C['opened']/1e3:.0f} тыс. т/год")
    print(f"  Астероид {C['ast_diam']/1e3:.0f} км, ρ={C['ast_rho']:.0f} кг/м³: объём "
          f"{C['ast_vol']/1e9:.2f} км³, масса {C['ast_mass_t']/1e9:.1f} млрд т; "
          f"покрывает сталь станции плюс замену за 200 лет в {C['ast_covers']:.1f} раза")
    print(f"  Плавка: {C['smelt_power_GW']:.1f} ГВт = "
          f"{C['smelt_share']*100:.2f} % полной мощности")

    D = RES['D_docking']
    print()
    print('=' * 74)
    print('D. СТЫКОВОЧНЫЙ МОДУЛЬ')
    print('=' * 74)
    print(f"  Кольцо Ø{D['ring_d']:.0f} м: площадь {D['ring_area']:,.0f} м², "
          f"длина {D['ring_circ']:.0f} м")
    print(f"  {D['n_strut']} радиальных элемента, сечение ~{D['strut_section']:.1f} м² "
          f"каждый, суммарно {D['strut_area']:.0f} м²")
    print(f"  Заселение: {D['settle_rate']:,.0f} человек/сут на цилиндр; "
          f"карантин {D['quar_days']:.0f} сут требует "
          f"{D['quar_places']:,.0f} мест")
    print(f"  Модуль {D['dock_mass']:,.0f} т; {D['airlocks']} шлюза по "
          f"{D['airlock_vol']:.0f} м³ = {D['airlock_tot']:,.0f} м³ "
          f"({D['air_mass']/1e3:.1f} т воздуха)")
    print(f"  Окружная скорость обшивки {D['v_shell_kmh']:.0f} км/ч — "
          f"стыковка только на неподвижной раме")
    print(f"  Грузооборот {D['cargo_yr']/1e6:.1f} млн т/год = "
          f"{D['cargo_day']:,.0f} т/сут")

    E = RES['E_cats']
    print()
    print('=' * 74)
    print('E. КОШКИ')
    print('=' * 74)
    print(f"  Зерно в хранилище {E['grain_t']/1e3:.0f} тыс. т, объём "
          f"{E['grain_vol']/1e3:.0f} тыс. м³, площадь {E['store_area']/1e6:.3f} км²")
    print(f"  Поголовье {E['cats_total']:,.0f} голов "
          f"({E['cats_per_cyl']:,.0f} на цилиндр), {E['cats_share_of_population']*100:.1f} % населения")
    print(f"  Корм {E['cat_kcal_day']:.0f} ккал/сут → {E['cat_food_t']:.1f} т/год, "
          f"белка {E['cat_prot_t']:.1f} т/год, животного {E['cat_meat_t']:.1f} т/год")
    print(f"  Источники: отходы разделки рыбы {E['fish_waste']/1e3:.0f} тыс. т, "
          f"мука из личинок {E['bsf_for_cats']:.0f} т/год")
    print(f"  Служебная потребность: {E['cat_per_store_area']} м² хранилища на кота → "
          f"{E['cats_store']:.0f} голов; остальные {E['cats_pet']:,.0f} — содержание")
    print(f"  Носители токсоплазмоза {E['toxo_share']*100:.0f} % поголовья")

    F = RES['F_insects']
    print()
    print('=' * 74)
    print('F. НАСЕКОМЫЕ')
    print('=' * 74)
    print(f"  Пчёлы {F['bees_total']:,} семей, мёда {F['honey_t']:.0f} т/год "
          f"({F['honey_per_colony_kg']:.1f} кг на семью)")
    print(f"  Опыляемые площади {F['pollinated']:.0f} км² "
          f"({F['pollinated_share']*100:.0f} % посевов)")
    print(f"  Шмели {F['bumble_colonies']:,.0f} семей на {F['greenhouse']:.0f} км²")
    print(f"  Чёрная львинка: сырьё {F['bsf_feed']/1e3:.0f} тыс. т/год → сухая "
          f"личинка {F['bsf_larva']/1e3:.1f} тыс. т/год, белка "
          f"{F['bsf_prot_t']/1e3:.1f} тыс. т/год")
    print(f"  На кошек уходит {F['bsf_for_cats']:.0f} т/год; остаётся "
          f"{F['bsf_left']/1e3:.1f} тыс. т/год")
    print(f"  Потребность в корме: рыба {F['fish_feed']/1e3:.0f} тыс. т/год, "
          f"птица {F['chick_feed']/1e3:.0f} тыс. т/год")
    print(f"  Покрытие из личинок: {F['feed_from_bsf']/1e3:.1f} тыс. т/год, "
          f"недостача {F['feed_shortfall']/1e3:.1f} тыс. т/год")

    G = RES['G_cities']
    print()
    print('=' * 74)
    print('G. ГОРОДА')
    print('=' * 74)
    print(f"  Обитаемая площадь {G['area_tot']:,.1f} км²; плотность "
          f"{G['density']:.0f} человек/км²")
    print(f"  Застройка {G['urban_area']:.0f} км² ({G['urban_share']*100:.1f} %), "
          f"открытые пространства {G['park_area']:.0f} км²")
    print(f"  Города по {G['city_pop']:,} человек: {G['n_cities']:.0f} шт. по "
          f"{G['city_area']:.1f} км² (радиус {G['city_radius']:.2f} км)")
    for sc in (1, 100, 200, 1000, 2000):
        m = G['mc'][sc]
        extra = ''
        if sc == 1:
            extra = (f"; высота {m['blocks_dia']:.0f} блоков при пределе "
                     f"{G['mc_height']} → {'помещается' if m.get('fits_height') else 'НЕ помещается'}")
        print(f"  Minecraft 1:{sc}: {m['blocks_len']:.0f} × {m['blocks_dia']:.0f} блоков, "
              f"поверхность {m['surface']:,.0f} блоков{extra}")
    print(f"  Рекомендуемый 1:{G['mc_recommended']}: {G['mc_rec_len']:.0f} × "
          f"{G['mc_rec_dia']:.0f} блоков, {G['mc_rec_surface']:,.0f} блоков "
          f"поверхности")
    print(f"  Район 1 км² при 1:{G['mc_district_scale']}: "
          f"{G['mc_district_blocks']:.0f} × {G['mc_district_blocks']:.0f} блоков")
    print(f"  Полный объём при 1:1: {G['mc_1to1_surface']/1e6:.0f} млн блоков "
          f"поверхности")

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(RES, f, ensure_ascii=False, indent=1, default=str)
    print()
    print(f'Результаты сохранены: {OUT}')
