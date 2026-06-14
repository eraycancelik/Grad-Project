"""
R134a Buhar Sıkıştırmalı Soğutma Çevrimi - El Hesabı için Durum Noktaları
Case: T_evap = -30°C, T_cond = 30°C, superheat = 3°C, subcooling = 3°C, eta = 0.85
"""
 
from CoolProp.CoolProp import PropsSI
 
# ─────────────────────────────────────────
# PARAMETRELER
# ─────────────────────────────────────────
akiskan   = "R134a"
T_evap    = -30 + 273.15   # K
T_cond    = 30  + 273.15   # K
superheat = 3               # °C
subcooling= 3               # °C
eta       = 0.85            # kompresör isentropik verimi
T0        = 25  + 273.15   # K  (ölü hal)
P0        = 101325          # Pa (ölü hal)
 
# ─────────────────────────────────────────
# BASINÇLAR (doyma basınçları)
# ─────────────────────────────────────────
P_evap = PropsSI("P", "T", T_evap, "Q", 1, akiskan)
P_cond = PropsSI("P", "T", T_cond, "Q", 1, akiskan)
 
print("=" * 55)
print("  BASINÇLAR")
print("=" * 55)
print(f"  P_evap ({-30}°C doyma) = {P_evap/1e5:.4f} bar")
print(f"  P_cond ({+30}°C doyma) = {P_cond/1e5:.4f} bar")
print(f"  Basınç oranı          = {P_cond/P_evap:.4f}")
 
# ─────────────────────────────────────────
# NOKTA 1 — Kompresör Girişi (kızgın buhar)
# ─────────────────────────────────────────
T1 = T_evap + superheat   # K
h1 = PropsSI("H", "T", T1, "P", P_evap, akiskan) / 1000   # kJ/kg
s1 = PropsSI("S", "T", T1, "P", P_evap, akiskan) / 1000   # kJ/kg·K
 
print("\n" + "=" * 55)
print("  NOKTA 1 — Kompresör Girişi")
print(f"  Durum  : Kızgın Buhar")
print(f"  T1     = {T1 - 273.15:.1f} °C   ({-30}+{superheat})")
print(f"  P1     = {P_evap/1e5:.4f} bar")
print(f"  h1     = {h1:.4f} kJ/kg")
print(f"  s1     = {s1:.6f} kJ/kg·K")
 
# ─────────────────────────────────────────
# NOKTA 2s — İdeal Kompresör Çıkışı (isentropik)
# ─────────────────────────────────────────
h2s = PropsSI("H", "P", P_cond, "S", s1 * 1000, akiskan) / 1000
T2s = PropsSI("T", "P", P_cond, "S", s1 * 1000, akiskan) - 273.15
s2s = s1   # isentropik → entropi değişmez
 
print("\n" + "=" * 55)
print("  NOKTA 2s — İdeal Kompresör Çıkışı (isentropik)")
print(f"  Durum  : Kızgın Buhar")
print(f"  T2s    = {T2s:.2f} °C")
print(f"  P2s    = {P_cond/1e5:.4f} bar")
print(f"  h2s    = {h2s:.4f} kJ/kg")
print(f"  s2s    = {s2s:.6f} kJ/kg·K  (s2s = s1)")
 
# ─────────────────────────────────────────
# NOKTA 2 — Gerçek Kompresör Çıkışı
# ─────────────────────────────────────────
w_isen = h2s - h1
w_comp = w_isen / eta
h2     = h1 + w_comp
s2     = PropsSI("S", "P", P_cond, "H", h2 * 1000, akiskan) / 1000
T2     = PropsSI("T", "P", P_cond, "H", h2 * 1000, akiskan) - 273.15
 
print("\n" + "=" * 55)
print("  NOKTA 2 — Gerçek Kompresör Çıkışı")
print(f"  Durum  : Kızgın Buhar")
print(f"  T2     = {T2:.2f} °C")
print(f"  P2     = {P_cond/1e5:.4f} bar")
print(f"  h2     = {h2:.4f} kJ/kg")
print(f"  s2     = {s2:.6f} kJ/kg·K")
print(f"  w_isen = h2s - h1 = {h2s:.4f} - {h1:.4f} = {w_isen:.4f} kJ/kg")
print(f"  w_comp = w_isen / η = {w_isen:.4f} / {eta} = {w_comp:.4f} kJ/kg")
 
# ─────────────────────────────────────────
# NOKTA 3 — Valf Girişi (sıkıştırılmış sıvı)
# ─────────────────────────────────────────
T3 = T_cond - subcooling   # K
h3 = PropsSI("H", "T", T3, "P", P_cond, akiskan) / 1000
s3 = PropsSI("S", "T", T3, "P", P_cond, akiskan) / 1000
 
print("\n" + "=" * 55)
print("  NOKTA 3 — Valf Girişi (alt soğutmalı sıvı)")
print(f"  Durum  : Sıkıştırılmış Sıvı")
print(f"  T3     = {T3 - 273.15:.1f} °C   ({+30}-{subcooling})")
print(f"  P3     = {P_cond/1e5:.4f} bar")
print(f"  h3     = {h3:.4f} kJ/kg")
print(f"  s3     = {s3:.6f} kJ/kg·K")
 
# ─────────────────────────────────────────
# NOKTA 4 — Valf Çıkışı / Evaporatör Girişi
# ─────────────────────────────────────────
h4 = h3   # izoentalpik genleşme
s4 = PropsSI("S", "P", P_evap, "H", h4 * 1000, akiskan) / 1000
T4 = PropsSI("T", "P", P_evap, "H", h4 * 1000, akiskan) - 273.15
x4 = PropsSI("Q", "P", P_evap, "H", h4 * 1000, akiskan)
 
print("\n" + "=" * 55)
print("  NOKTA 4 — Valf Çıkışı / Evaporatör Girişi")
print(f"  Durum  : Sıvı-Buhar Karışımı")
print(f"  T4     = {T4:.2f} °C")
print(f"  P4     = {P_evap/1e5:.4f} bar")
print(f"  h4     = {h4:.4f} kJ/kg   (h4 = h3, izoentalpik)")
print(f"  s4     = {s4:.6f} kJ/kg·K")
print(f"  x4     = {x4:.4f}  (kuruluk derecesi)")
 
# ─────────────────────────────────────────
# PERFORMANS HESAPLARI
# ─────────────────────────────────────────
q_evap  = h1 - h4
q_cond  = h2 - h3
COP     = q_evap / w_comp
 
print("\n" + "=" * 55)
print("  PERFORMANS")
print("=" * 55)
print(f"  q_evap = h1 - h4 = {h1:.4f} - {h4:.4f} = {q_evap:.4f} kJ/kg")
print(f"  q_cond = h2 - h3 = {h2:.4f} - {h3:.4f} = {q_cond:.4f} kJ/kg")
print(f"  w_comp =           {w_comp:.4f} kJ/kg")
print(f"  COP    = q_evap / w_comp = {q_evap:.4f} / {w_comp:.4f} = {COP:.4f}")
 
# ─────────────────────────────────────────
# EKSERJİ HESAPLARI
# ─────────────────────────────────────────
# Ölü hal entalpisi ve entropisi
h0 = PropsSI("H", "T", T0, "P", P0, akiskan) / 1000
s0 = PropsSI("S", "T", T0, "P", P0, akiskan) / 1000
 
ex_dest_comp = T0 * (s2 - s1)
ex_dest_cond = T0 * (s3 - s2 + q_cond / T_cond)
ex_dest_evap = T0 * (s1 - s4 - q_evap / T_evap)
ex_dest_exp  = T0 * (s4 - s3)
ex_dest_total= ex_dest_comp + ex_dest_cond + ex_dest_evap + ex_dest_exp
 
eta_exergy = 1 - (ex_dest_total / w_comp)
 
print("\n" + "=" * 55)
print("  EKSERJİ YIKIMLARI  (T₀ = 25°C = 298.15 K)")
print("=" * 55)
print(f"  Kompresör     : T₀×(s2-s1)              = {ex_dest_comp:.4f} kJ/kg")
print(f"  Kondenser     : T₀×(s3-s2+qc/Tc)       = {ex_dest_cond:.4f} kJ/kg")
print(f"  Evaporatör    : T₀×(s1-s4-qe/Te)       = {ex_dest_evap:.4f} kJ/kg")
print(f"  Genleşme valfi: T₀×(s4-s3)              = {ex_dest_exp:.4f} kJ/kg")
print(f"  ─────────────────────────────────────────")
print(f"  Toplam       :                           = {ex_dest_total:.4f} kJ/kg")
print(f"\n  Ekserji verimi = 1 - (ex_total / w_comp)")
print(f"                 = 1 - ({ex_dest_total:.4f} / {w_comp:.4f})")
print(f"                 = {eta_exergy:.4f}  ({eta_exergy*100:.2f}%)")
 
# ─────────────────────────────────────────
# CSV İLE KARŞILAŞTIRMA
# ─────────────────────────────────────────
print("\n" + "=" * 55)
print("  CSV İLE KARŞILAŞTIRMA")
print("=" * 55)
print(f"  {'':20} {'Hesaplanan':>12} {'CSV':>12}")
print(f"  {'─'*44}")
print(f"  {'COP':20} {COP:>12.4f} {'2.6501':>12}")
print(f"  {'w_comp (kJ/kg)':20} {w_comp:>12.4f} {'54.8112':>12}")
print(f"  {'q_evap (kJ/kg)':20} {q_evap:>12.4f} {'145.2577':>12}")
print(f"  {'eta_exergy':20} {eta_exergy:>12.4f} {'0.6597':>12}")
print(f"  {'ex_dest_comp':20} {ex_dest_comp:>12.4f} {'7.6335':>12}")