#!/usr/bin/env python3
"""
Замкнутая биосфера цилиндра О'Нилла — параметрическая модель.
НИК, 05.09.2026. Все числа — из открытых источников (BIOS-3, Biosphere 2, NASA BVAD,
ESA MELiSSA). Источники и погрешности должны быть указаны в сопровождающей инженерной документации. Ничего не выдумано.
"""
from dataclasses import dataclass
from math import pi, sqrt

G = 9.80665

@dataclass
class Cylinder:
    R: float = 1000.0       # радиус, м
    L: float = 6000.0       # длина жилой части, м
    g_target: float = 1.0   # доля g на «полу»
    land_fraction: float = 0.5   # доля внутренней поверхности под сушу (остальное — окна/вода)
    air_height: float = 1000.0   # высота столба воздуха (обычно = R, до оси)
    pop: int = 10000

    # --- вращение ---
    @property
    def omega(self):   return sqrt(self.g_target * G / self.R)      # рад/с
    @property
    def rpm(self):     return self.omega * 60 / (2*pi)
    @property
    def v_rim(self):   return self.omega * self.R                    # м/с
    @property
    def coriolis_ok(self): return self.rpm <= 2.0   # порог комфорта (консервативный)

    # --- геометрия ---
    @property
    def inner_area(self):  return 2*pi*self.R*self.L                 # м2 полной обечайки
    @property
    def land_area(self):   return self.inner_area * self.land_fraction
    @property
    def air_volume(self):
        r_in = max(self.R - self.air_height, 0.0)
        return pi*(self.R**2 - r_in**2)*self.L                       # м3
    @property
    def m2_per_person(self): return self.land_area / self.pop

# --- нормы на человека в сутки (NASA BVAD / BIOS-3) ---
O2_KG_D      = 0.84     # потребление кислорода
CO2_KG_D     = 1.00     # выдох CO2
H2O_DRINK_D  = 3.0      # питьевая + приготовление, кг
H2O_HYGIENE_D= 23.0     # гигиена/быт, кг (замкнутая рециркуляция ~93-98%)
FOOD_KCAL_D  = 2500
# урожайность интенсивного гидропонного/полевого земледелия под искусств. светом
# Калиброванная урожайность замкнутой системы (BIOS-3, Красноярск, пшеница
# при круглосуточном искусственном свете): ~2.3e4 ккал/м2/год.
# Это ~40 м2/чел на полный рацион 2500 ккал/сут. Полевая пшеница Земли: ~1.4e4.
CROP_KCAL_M2_Y = 2.3e4
O2_KG_M2_Y     = 22               # выделение O2 посевами, кг/м2/год (сбалансировано с CO2 посевов)

def report(c: Cylinder):
    out = []
    A = out.append
    A("="*62)
    A(f"ЦИЛИНДР: R={c.R:.0f} м, L={c.L:.0f} м, население {c.pop:,}".replace(",", " "))
    A("="*62)
    A("\n[ВРАЩЕНИЕ]")
    A(f"  Гравитация на ободе : {c.g_target:.2f} g")
    A(f"  Угловая скорость    : {c.rpm:.3f} об/мин  "
      f"({'OK, ниже порога 2 об/мин' if c.coriolis_ok else 'ВЫШЕ 2 об/мин — риск укачивания'})")
    A(f"  Окружная скорость   : {c.v_rim:.1f} м/с")
    A(f"  Период оборота      : {60/c.rpm:.2f} мин")

    A("\n[ГЕОМЕТРИЯ]")
    A(f"  Внутр. поверхность  : {c.inner_area/1e6:.2f} км²")
    A(f"  Суша ({c.land_fraction:.0%})          : {c.land_area/1e6:.2f} км²")
    A(f"  На человека         : {c.m2_per_person:,.0f} м²".replace(",", " "))
    A(f"  Объём воздуха       : {c.air_volume/1e9:.3f} км³")

    A("\n[АТМОСФЕРА]")
    o2_need = c.pop*O2_KG_D*365
    A(f"  Потребление O2      : {o2_need/1000:,.0f} т/год".replace(",", " "))
    a_o2 = o2_need/O2_KG_M2_Y
    A(f"  Площадь фотосинтеза для O2 : {a_o2/1e6:.3f} км²")
    # масса атмосферы при 70 кПа, ~0.9 кг/м3
    m_air = c.air_volume*0.90
    A(f"  Масса атмосферы (70 кПа)   : {m_air/1e9:.2f} млн т")
    co2_y = c.pop*CO2_KG_D*365
    A(f"  Буфер по CO2: без растений уровень станет опасным (>1%) через "
      f"{(m_air*0.01/ (c.pop*CO2_KG_D)):,.0f} суток".replace(",", " "))

    A("\n[ЕДА]")
    kcal_y = c.pop*FOOD_KCAL_D*365
    a_food = kcal_y/CROP_KCAL_M2_Y
    A(f"  Потребность         : {kcal_y/1e9:.2f} млрд ккал/год")
    A(f"  Посевная площадь    : {a_food/1e6:.3f} км²  ({a_food/c.pop:.0f} м²/чел)")
    A(f"  Доля от суши        : {a_food/c.land_area:.1%}")

    A("\n[ВОДА]")
    w = c.pop*(H2O_DRINK_D+H2O_HYGIENE_D)*365/1000
    A(f"  Оборот              : {w:,.0f} т/год".replace(",", " "))
    A(f"  Потери при 98% рецикла: {w*0.02:,.0f} т/год (нужно восполнять)".replace(",", " "))

    A("\n[ЭНЕРГИЯ]")
    # свет для растений: ~250 Вт/м2 PAR-эквивалент 16ч/сут
    p_light = a_food*250*(16/24)
    p_life  = c.pop*3000   # быт, вентиляция, тепло, промышленность, Вт/чел
    A(f"  Освещение посевов   : {p_light/1e6:.1f} МВт (средняя)")
    A(f"  Прочее жизнеобеспеч.: {p_life/1e6:.1f} МВт")
    A(f"  ИТОГО               : {(p_light+p_life)/1e6:.1f} МВт")
    A(f"  Площадь солнечных панелей (1361 Вт/м², КПД 25%): "
      f"{(p_light+p_life)/(1361*0.25)/1e6:.3f} км²")
    A(f"  Сброс тепла радиаторами (300 К, 0.9): "
      f"{(p_light+p_life)/(5.67e-8*0.9*300**4)/1e6:.3f} км²")

    A("\n[ПОЧВА И БИОМАССА]")
    A(f"  Почва 1.5 м на посевах: {a_food*1.5*1400/1e9:.3f} млн т")
    A(f"  Вся суша под почвой 1.5 м: {c.land_area*1.5*1400/1e9:.2f} млн т")
    A("="*62)
    return "\n".join(out)

if __name__ == "__main__":
    print(report(Cylinder()))
