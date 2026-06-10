import CoolProp.CoolProp as CP

def get_critical_temp(fluid):
    """Akışkanın kritik sıcaklığını Celsius cinsinden döndür."""
    return CP.PropsSI('Tcrit', fluid) - 273.15

def is_transcritical(fluid, T_cond_C):
    """Çevrimin transkritik olup olmadığını kontrol et."""
    T_crit = get_critical_temp(fluid)
    return T_cond_C > T_crit

def vapor_compression_cycle(refrigerant, T_evap_C, T_cond_C,
                             superheat=7.0, subcooling=5.0,
                             eta_isentropic=0.85,
                             T0_C=25.0, P0=101325.0):
    """
    Buhar sıkıştırmalı soğutma çevrimi analizi.

    Durum noktaları (De Paula et al. 2020 gösterimine uygun):
        1 → Kompresör girişi (evaporatör çıkışı, süper ısıtılmış buhar)
        2 → Kompresör çıkışı (kondenser/gaz soğutucu girişi)
        3 → Kondenser çıkışı (alt soğutulmuş sıvı veya gaz soğutucu çıkışı)
        4 → Genleşme valfi çıkışı (evaporatör girişi)

    Parametreler
    ─────────────
    refrigerant    : str   – CoolProp akışkan adı
    T_evap_C       : float – Evaporasyon sıcaklığı [°C]
    T_cond_C       : float – Kondensasyon/gaz soğutucu sıcaklığı [°C]
    superheat      : float – Süper ısıtma derecesi [°C/K]
    subcooling     : float – Alt soğutma derecesi [°C/K]
    eta_isentropic : float – Kompresör isentropik verimi [-]
    T0_C           : float – Ölü hal sıcaklığı [°C]
    P0             : float – Ölü hal basıncı [Pa]

    Dönüş değeri : dict
    """
    T_evap = T_evap_C + 273.15
    T_cond = T_cond_C + 273.15
    T0     = T0_C + 273.15

    transcritical = is_transcritical(refrigerant, T_cond_C)

    # Basınçlar
    P_evap = CP.PropsSI('P', 'T', T_evap, 'Q', 1, refrigerant)

    if transcritical:
        # R744 transkritik: gaz soğutucu basıncı (Kim et al. 2009)
        P_cond = (1.938 * T_cond_C + 9.872) * 1e5  # bar → Pa
    else:
        P_cond = CP.PropsSI('P', 'T', T_cond, 'Q', 0, refrigerant)

    # ── Durum 1: Kompresör girişi (süper ısıtılmış buhar) ──
    T1 = T_evap + superheat
    h1 = CP.PropsSI('H', 'T', T1, 'P', P_evap, refrigerant)
    s1 = CP.PropsSI('S', 'T', T1, 'P', P_evap, refrigerant)

    # ── Durum 2: Kompresör çıkışı ──
    h2s = CP.PropsSI('H', 'P', P_cond, 'S', s1, refrigerant)
    h2  = h1 + (h2s - h1) / eta_isentropic
    s2  = CP.PropsSI('S', 'H', h2, 'P', P_cond, refrigerant)
    T2  = CP.PropsSI('T', 'H', h2, 'P', P_cond, refrigerant)

    # ── Durum 3: Kondenser/gaz soğutucu çıkışı ──
    if transcritical:
        T3 = T_cond - subcooling          # gaz soğutucu çıkışı
        h3 = CP.PropsSI('H', 'T', T3, 'P', P_cond, refrigerant)
        s3 = CP.PropsSI('S', 'T', T3, 'P', P_cond, refrigerant)
    else:
        T3 = T_cond - subcooling          # alt soğutulmuş sıvı
        h3 = CP.PropsSI('H', 'T', T3, 'P', P_cond, refrigerant)
        s3 = CP.PropsSI('S', 'T', T3, 'P', P_cond, refrigerant)

    # ── Durum 4: Genleşme valfi çıkışı (izoentalpik) ──
    h4 = h3
    s4 = CP.PropsSI('S', 'H', h4, 'P', P_evap, refrigerant)
    T4 = CP.PropsSI('T', 'H', h4, 'P', P_evap, refrigerant)

    # ── Enerji hesapları ──
    w_comp = h2 - h1          # Kompresör işi [J/kg]
    q_evap = h1 - h4          # Soğutma etkisi [J/kg]
    q_cond = h2 - h3          # Kondenser ısısı [J/kg]
    COP    = q_evap / w_comp

    # ── Ekserji analizi (De Paula et al. 2020, Denklem 23-27) ──
    h0 = CP.PropsSI('H', 'T', T0, 'P', P0, refrigerant)
    s0 = CP.PropsSI('S', 'T', T0, 'P', P0, refrigerant)

    def specific_exergy(h, s):
        return (h - h0) - T0 * (s - s0)

    ex1 = specific_exergy(h1, s1)
    ex2 = specific_exergy(h2, s2)
    ex3 = specific_exergy(h3, s3)
    ex4 = specific_exergy(h4, s4)

    # Referans sıcaklık
    T_ref = T_cond if transcritical else T_cond  # 45°C referans (transkritik için)

    # Ekserji yıkımları [J/kg]
    ex_dest_comp = (ex1 - ex2) + w_comp                          # Denklem 23
    ex_dest_cond = (ex2 - ex3) - q_cond * (1 - T0 / T_ref)      # Denklem 24
    ex_dest_evap = (ex4 - ex1) + q_evap * (1 - T0 / T_evap)     # Denklem 25
    ex_dest_exp  = ex3 - ex4                                      # Denklem 26
    ex_dest_total = ex_dest_comp + ex_dest_cond + ex_dest_evap + ex_dest_exp

    # Ekserji verimi (Denklem 22)
    eta_exergy = 1.0 - ex_dest_total / w_comp

    # Basınç oranı
    pressure_ratio = P_cond / P_evap

    return {
        # Enerji
        'COP':              round(COP, 4),
        'q_evap_kJ':        round(q_evap / 1000, 4),
        'w_comp_kJ':        round(w_comp / 1000, 4),
        'q_cond_kJ':        round(q_cond / 1000, 4),
        # Termodinamik durum noktaları
        'h1_kJ':            round(h1 / 1000, 2),
        'h2_kJ':            round(h2 / 1000, 2),
        'h3_kJ':            round(h3 / 1000, 2),
        'h4_kJ':            round(h4 / 1000, 2),
        'T1_C':             round(T1 - 273.15, 2),
        'T2_C':             round(T2 - 273.15, 2),
        'T3_C':             round(T3 - 273.15, 2),
        'T4_C':             round(T4 - 273.15, 2),
        'P_evap_kPa':       round(P_evap / 1000, 2),
        'P_cond_kPa':       round(P_cond / 1000, 2),
        'pressure_ratio':   round(pressure_ratio, 3),
        # Ekserji
        'ex_dest_comp_kJ':  round(ex_dest_comp / 1000, 4),
        'ex_dest_cond_kJ':  round(ex_dest_cond / 1000, 4),
        'ex_dest_evap_kJ':  round(ex_dest_evap / 1000, 4),
        'ex_dest_exp_kJ':   round(ex_dest_exp  / 1000, 4),
        'ex_dest_total_kJ': round(ex_dest_total / 1000, 4),
        'eta_exergy':       round(eta_exergy, 4),
        # Meta
        'transcritical':    transcritical,
        'refrigerant':      refrigerant,
    }
