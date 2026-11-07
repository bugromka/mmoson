# -*- coding: utf-8 -*-
"""
ММОСО'Н — редакция 8: проверочные расчёты и явно маркированные сценарии.

Области:
  A. Генетика замкнутой популяции
  B. Пищевая потребность, целевой инвентарь и статус сверки потоков
  C. Промышленность и отходы
  D. Стыковочный модуль
  E–F. Экосистемные сценарии, не считающиеся утверждённым кормовым планом

Пищевые площади и выпуск не оптимизируются: пока не согласованы состав рациона,
нутриенты, съедобные доли, кормовые потоки, потери и складская ротация,
итоговый производственный план вычислять нельзя. Старые сценарные значения
сохранены только в блоке legacy_scenario и не являются проектными целями.
"""
import json
import math
import os


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'edition8_results.json')

# ═════════════════════════════════════════════════════════════
# Исходные величины публикации и новые сценарные допущения
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

# Старые площади/выпуски сохранены лишь как архивные значения, не как план.
LEGACY_FARM_TOT = 1508.0       # км², бывшая таблица 5.5
LEGACY_FARM_AGRI = 972.0       # км², бывшая таблица 5.5
LEGACY_CROP_AREA = 807.0       # км², бывшая таблица 5.4
LEGACY_FAST_RESERVE = 150.0    # км², бывшая таблица 5.5

# Явные демографические и активностные допущения по FAO/WHO/UNU [40].
SEX_WEIGHTS = {"men": 0.5, "women": 0.5}
AGE_WEIGHTS = {"18-29.9": 0.5, "30-59.9": 0.5}
BMI = 21.0
PAL = 1.75
ENERGY_MALE_18_29 = 2800.0
ENERGY_MALE_30_59 = 2750.0
ENERGY_FEMALE_18_29 = 2300.0
ENERGY_FEMALE_30_59 = 2250.0
KCAL_DAY = (
    ((ENERGY_MALE_18_29 + ENERGY_MALE_30_59) / 2) * SEX_WEIGHTS["men"]
    + ((ENERGY_FEMALE_18_29 + ENERGY_FEMALE_30_59) / 2) * SEX_WEIGHTS["women"]
)
CAL_NEED = N_TOT * KCAL_DAY * 365.0
PROT_DAY = 70.0             # г/(чел.·сут), отдельное планировочное допущение
PROT_NEED = N_TOT * PROT_DAY * 365.0 / 1e6  # т/год
CAL_STOCK_MULTIPLIER = 1.5
PROT_STOCK_MULTIPLIER = 1.3
CAL_STOCK_TARGET = CAL_NEED * CAL_STOCK_MULTIPLIER
PROT_STOCK_TARGET = PROT_NEED * PROT_STOCK_MULTIPLIER

# Legacy system/crop totals are kept for traceability and discrepancy reporting.
LEGACY_CROP_GROSS_KCAL = 2.216e12
LEGACY_SYSTEM_GROSS_KCAL = 2.338e12
LEGACY_SYSTEM_NET_KCAL = 1.870e12
LEGACY_SYSTEM_GROSS_PROTEIN_T = 87_200.0
LEGACY_SYSTEM_NET_PROTEIN_T = 69_800.0
LEGACY_AGGREGATE_LOSS = 0.20
LEGACY_FISH_SECTION3_T = 25_000.0
LEGACY_FISH_SECTION5_T = 70_000.0
LEGACY_PROTEIN_DISCREPANCY_T = 2_020.0

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
# B. ПИЩЕВАЯ ПОТРЕБНОСТЬ И СВЕРКА ПОТОКОВ
# ═════════════════════════════════════════════════════════════
assert math.isclose(KCAL_DAY, 2525.0, abs_tol=1e-9)
assert math.isclose(CAL_NEED, 921_625_000_000.0, abs_tol=0.1)
assert math.isclose(PROT_NEED, 25_550.0, abs_tol=1e-9)

RES['B_agriculture'] = dict(
    status="needs and stock references only; production plan not calculated",
    population=N_TOT,
    energy_kcal_per_person_day=KCAL_DAY,
    energy_need_kcal_year=CAL_NEED,
    energy_assumptions=dict(
        source="FAO/WHO/UNU Human energy requirements (2004), chapters 5–6 [40]",
        sex_weights=SEX_WEIGHTS,
        age_weights=AGE_WEIGHTS,
        bmi=BMI,
        pal=PAL,
        male_kcal_day_by_age={"18-29.9": ENERGY_MALE_18_29, "30-59.9": ENERGY_MALE_30_59},
        female_kcal_day_by_age={"18-29.9": ENERGY_FEMALE_18_29, "30-59.9": ENERGY_FEMALE_30_59},
        derivation="equal-weighted mean of the two age groups and sexes",
    ),
    protein_g_per_person_day=PROT_DAY,
    protein_assumption_status="separate provisional assumption; not derived from the energy estimate",
    protein_need_t_year=PROT_NEED,
    calorie_inventory_multiplier=CAL_STOCK_MULTIPLIER,
    calorie_inventory_target_kcal=CAL_STOCK_TARGET,
    protein_inventory_multiplier=PROT_STOCK_MULTIPLIER,
    protein_inventory_target_t=PROT_STOCK_TARGET,
    annual_gross_output_status="unreconciled; not reported as a current value",
    annual_net_output_status="not calculated until product flows and edible yields are reconciled",
    loss_fraction=None,
    loss_status="not validated by product and process stage",
    final_crop_area_km2=None,
    final_crop_output_t_year=None,
    production_plan_approved=False,
    unresolved_discrepancies=dict(
        fish_section3_t=LEGACY_FISH_SECTION3_T,
        fish_section5_t=LEGACY_FISH_SECTION5_T,
        fish_difference_t=LEGACY_FISH_SECTION5_T-LEGACY_FISH_SECTION3_T,
        former_protein_discrepancy_t=LEGACY_PROTEIN_DISCREPANCY_T,
    ),
    legacy_scenario=dict(
        status="archived only; not an approved plan, recommendation, or current output",
        crop_area_km2=LEGACY_CROP_AREA,
        farmland_total_km2=LEGACY_FARM_TOT,
        farmland_agricultural_use_km2=LEGACY_FARM_AGRI,
        crop_gross_kcal_year=LEGACY_CROP_GROSS_KCAL,
        system_gross_kcal_year=LEGACY_SYSTEM_GROSS_KCAL,
        system_net_kcal_year=LEGACY_SYSTEM_NET_KCAL,
        system_gross_protein_t_year=LEGACY_SYSTEM_GROSS_PROTEIN_T,
        system_net_protein_t_year=LEGACY_SYSTEM_NET_PROTEIN_T,
        unvalidated_aggregate_loss_fraction=LEGACY_AGGREGATE_LOSS,
        maize_area_km2=150.0,
        maize_share_of_former_crop_area=150.0/LEGACY_CROP_AREA,
        theoretical_areas_and_optimisations="not recalculated; former values are not recommendations",
    ),
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
    waste_flow_status="scenario partition only; not an approved waste-processing or feed-production plan",
    waste_total=WASTE_TOT, waste_org=WASTE_ORG,
    waste_metglass=WASTE_METGLASS, waste_rest=WASTE_REST,
    sewage=SEWAGE_TOT,
    met_recovered=MET_REC, glass_recovered=GLASS_REC, rest_lost=REST_LOST,
    compost=COMPOST_T, bsf_substrate_input_scenario_t=BSF_FEED, biogas=BIOGAS,
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

FAST_TRANSFER_DAYS = 7.7  # transport-limit comparison; not the selected settlement flow
QUAR_DAYS = 40
ANNUAL_SETTLEMENT_FLOW = 100_000.0
PLANNED_FLOW_PER_DAY = round(ANNUAL_SETTLEMENT_FLOW / 365.0)
PLANNED_QUARANTINE_PLACES = round(ANNUAL_SETTLEMENT_FLOW * QUAR_DAYS / 365.25)
FAST_TRANSFER_RATE_PER_CYL = N_PER_CYL / FAST_TRANSFER_DAYS
FAST_TRANSFER_QUARANTINE_PLACES = round(N_PER_CYL * QUAR_DAYS / FAST_TRANSFER_DAYS)
assert PLANNED_QUARANTINE_PLACES == 10_951

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
    annual_quarantine_flow_people_year=ANNUAL_SETTLEMENT_FLOW,
    quarantine_flow_people_day=PLANNED_FLOW_PER_DAY,
    quarantine_hold_days=QUAR_DAYS,
    quarantine_places_concurrent=PLANNED_QUARANTINE_PLACES,
    transport_max_transfer_days=FAST_TRANSFER_DAYS,
    transport_max_flow_people_day_per_cylinder=FAST_TRANSFER_RATE_PER_CYL,
    fast_transfer_quarantine_places_counterfactual=FAST_TRANSFER_QUARANTINE_PLACES,
    fast_transfer_status="overload comparison only; not the selected settlement plan",
    dock_mass=DOCK_MASS, airlocks=AIRLOCKS, airlock_vol=AIRLOCK_VOL,
    airlock_tot=AIRLOCK_TOT, air_mass=AIR_MASS,
    dock_energy_GJ=DOCK_ENERGY_GJ,
    cargo_yr=CARGO_YR, cargo_day=CARGO_DAY,
    v_shell=V_SHELL, v_shell_kmh=V_SHELL_KMH,
    l_tot=L_TOT, d_axis=D_AXIS,
)

# ═════════════════════════════════════════════════════════════
# E. КОШКИ В ЭКОСИСТЕМЕ — ЧИСЛЕННОСТЬ ТОЛЬКО КАК СЦЕНАРИЙ
# ═════════════════════════════════════════════════════════════
CAT_PER_1000 = 6.0
CATS_TOT = N_TOT / 1000 * CAT_PER_1000
CATS_CYL = CATS_TOT / N_CYL
RES['E_cats'] = dict(
    status="illustrative population assumption only; feed and inventory flows not calculated",
    cats_per_1000=CAT_PER_1000,
    cats_total=CATS_TOT,
    cats_per_cyl=CATS_CYL,
    annual_feed_t=None,
    feed_energy_kcal=None,
    food_stock_t=None,
    feed_flow_status="requires an agreed diet, nutrient basis, edible fractions, and feed allocation",
)

# ═════════════════════════════════════════════════════════════
# F. НАСЕКОМЫЕ — КОРМОВЫЕ ПОТОКИ ОСТАЮТСЯ НЕСОГЛАСОВАННЫМИ
# ═════════════════════════════════════════════════════════════
BEES_TOT = BEES_PER_CYL * N_CYL
RES['F_insects'] = dict(
    status="candidate ecological functions; production/feed totals are not a plan",
    bee_colonies_scenario=BEES_TOT,
    honey_t_year=None,
    pollinated_area_km2=None,
    bumblebee_colonies=None,
    black_soldier_fly_feed_t_year=None,
    fish_and_poultry_feed_t_year=None,
    flow_status="biomass conversion, food-safety, feed demand and nutrient flows require reconciliation",
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
    print('B. ПИЩЕВАЯ ПОТРЕБНОСТЬ И СВЕРКА ПОТОКОВ')
    print('=' * 74)
    print(f"  Население {B['population']:,}; энергопотребление {B['energy_kcal_per_person_day']:.0f} ккал/(чел.·сут).")
    print("  Допущения: равные веса полов и возрастов 18–29,9 / 30–59,9 лет; BMI=21; PAL=1,75; FAO/WHO/UNU [40].")
    print(f"  Годовая потребность: {B['energy_need_kcal_year']/1e12:.6f} трлн ккал; белок {B['protein_need_t_year']:,.0f} т/год (70 г/(чел.·сут), отдельное допущение).")
    print(f"  Ориентир инвентаря: {B['calorie_inventory_target_kcal']/1e12:.7f} трлн ккал (×{B['calorie_inventory_multiplier']:.1f}); "
          f"{B['protein_inventory_target_t']:,.0f} т белка (×{B['protein_inventory_multiplier']:.1f}). Это запас, не годовой выпуск.")
    print("  Годовой валовой/нетто-выпуск, продуктовые потери и итоговые площади/выпуск культур не рассчитываются до сверки потоков.")
    legacy = B['legacy_scenario']
    print(f"  Архив прежней модели (не план): {legacy['crop_area_km2']:.0f} км²; "
          f"культуры {legacy['crop_gross_kcal_year']/1e12:.3f} трлн ккал; "
          f"системный валовой/нетто-сценарий {legacy['system_gross_kcal_year']/1e12:.3f}/"
          f"{legacy['system_net_kcal_year']/1e12:.3f} трлн ккал; потери 20 % не проверены.")
    discrep = B['unresolved_discrepancies']
    print(f"  Несверенные рыбные строки: {discrep['fish_section3_t']:,.0f} против "
          f"{discrep['fish_section5_t']:,.0f} т/год (разница {discrep['fish_difference_t']:,.0f}); "
          f"бывшая белковая невязка {discrep['former_protein_discrepancy_t']:,.0f} т.")

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
    print(f"  Сценарное распределение бытовых отходов: металл {C['met_recovered']/1e3:.0f} тыс. т, "
          f"стекло {C['glass_recovered']/1e3:.0f} тыс. т, компост "
          f"{C['compost']/1e3:.0f} тыс. т, сырьё на переработку насекомыми "
          f"{C['bsf_substrate_input_scenario_t']/1e3:.0f} тыс. т (не готовый корм).")
    print(f"  Сценарный коэффициент возврата: {C['closure']*100:.1f} %; "
          f"незамкнутый остаток {C['opened']/1e3:.0f} тыс. т/год; потоки требуют проверки.")
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
    print(f"  Плановый карантинный поток {D['annual_quarantine_flow_people_year']:,.0f} человек/год "
          f"(около {D['quarantine_flow_people_day']:,.0f}/сут); выдержка "
          f"{D['quarantine_hold_days']:.0f} суток требует "
          f"{D['quarantine_places_concurrent']:,.0f} мест единовременно.")
    print(f"  Контрфактический предельный трансфер 500 000 человек за "
          f"{D['transport_max_transfer_days']:.1f} суток на цилиндр потребовал бы "
          f"{D['fast_transfer_quarantine_places_counterfactual']:,.0f} мест; это не выбранный план.")
    print(f"  Модуль {D['dock_mass']:,.0f} т; {D['airlocks']} шлюза по "
          f"{D['airlock_vol']:.0f} м³ = {D['airlock_tot']:,.0f} м³ "
          f"({D['air_mass']/1e3:.1f} т воздуха)")
    print(f"  Окружная скорость обшивки {D['v_shell_kmh']:.0f} км/ч — "
          f"стыковка только на неподвижной раме")
    print(f"  Грузооборот {D['cargo_yr']/1e6:.1f} млн т/год = "
          f"{D['cargo_day']:,.0f} т/сут")

    E = RES['E_cats']
    F = RES['F_insects']
    print()
    print('=' * 74)
    print('E–F. ЭКОСИСТЕМНЫЕ СЦЕНАРИИ')
    print('=' * 74)
    print(f"  Сценарное допущение численности кошек: {E['cats_total']:,.0f}; рацион, годовой корм и складской запас не рассчитаны.")
    print(f"  Пчёлы в прежнем сценарии: {F['bee_colonies_scenario']:,} семей; мёд, опылённые площади и личиночный корм не приняты как выпуск.")
    print("  Кормовая биомасса, конверсия, пищевые потоки и потери требуют отдельной санитарной и нутриентной сверки.")

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(RES, f, ensure_ascii=False, indent=1, default=str)
    print()
    print(f'Результаты сохранены: {OUT}')
