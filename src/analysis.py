import numpy as np
import pandas as pd
from src.config import REFRIGERANTS
from src.thermodynamics import vapor_compression_cycle

def compare_refrigerants(T_evap_C=-3, T_cond_C=45):
    """Tüm akışkanları aynı koşullarda karşılaştır."""
    print(f"\n{'═'*80}")
    print(f"  KARŞILAŞTIRMALI ANALİZ — Tev={T_evap_C}°C | Tcond={T_cond_C}°C")
    print(f"{'═'*80}")

    header = (f"{'Akışkan':<12} {'COP':>6} {'η_ex':>6} {'P_ev[kPa]':>10} "
              f"{'P_cd[kPa]':>10} {'P_oran':>7} {'ExYık_top':>10} {'Trans':>6}")
    print(header)
    print("─"*80)

    all_results = {}
    for ref in REFRIGERANTS:
        try:
            r = vapor_compression_cycle(ref, T_evap_C, T_cond_C)
            all_results[ref] = r
            tr = "EVET" if r['transcritical'] else "HAYIR"
            print(f"{ref:<12} {r['COP']:>6.3f} {r['eta_exergy']:>6.3f} "
                  f"{r['P_evap_kPa']:>10.1f} {r['P_cond_kPa']:>10.1f} "
                  f"{r['pressure_ratio']:>7.2f} {r['ex_dest_total_kJ']:>10.2f} "
                  f"{tr:>6}")
        except Exception as e:
            print(f"{ref:<12} HATA: {e}")

    print("─"*80)

    # En iyi akışkan
    cops = {k: v['COP'] for k, v in all_results.items()}
    best = max(cops, key=cops.get)
    print(f"\n  ✓ En yüksek COP: {best} ({cops[best]:.3f})")
    ex_effs = {k: v['eta_exergy'] for k, v in all_results.items()}
    best_ex = max(ex_effs, key=ex_effs.get)
    print(f"  ✓ En yüksek Ekserji Verimi: {best_ex} ({ex_effs[best_ex]:.3f})")

    return all_results


def parametric_scan(T_evap_range=None, T_cond_range=None,
                    superheat_range=None, subcooling_range=None):
    """
    Farklı çalışma koşulları için büyük veri seti üret (ML için).
    """
    if T_evap_range   is None: T_evap_range   = np.arange(-30, 6, 5)
    if T_cond_range   is None: T_cond_range   = np.arange(30, 56, 5)
    if superheat_range is None: superheat_range = [3, 5, 7, 10]
    if subcooling_range is None: subcooling_range = [3, 5, 7]

    print(f"\n{'═'*60}")
    print("  PARAMETRİK TARAMA — Veri Seti Oluşturuluyor")
    print(f"  Tev: {T_evap_range[0]}…{T_evap_range[-1]}°C  "
          f"Tcond: {T_cond_range[0]}…{T_cond_range[-1]}°C")
    print(f"{'═'*60}")

    records = []
    total = (len(list(REFRIGERANTS)) * len(T_evap_range) *
             len(T_cond_range) * len(superheat_range) * len(subcooling_range))
    count = 0

    for ref in REFRIGERANTS:
        for Tev in T_evap_range:
            for Tcd in T_cond_range:
                for sh in superheat_range:
                    for sc in subcooling_range:
                        count += 1
                        try:
                            r = vapor_compression_cycle(
                                ref, float(Tev), float(Tcd),
                                superheat=float(sh), subcooling=float(sc))

                            # Sadece fiziksel olarak geçerli sonuçları al
                            if r['COP'] > 0 and r['eta_exergy'] > 0:
                                records.append({
                                    'refrigerant':      ref,
                                    'T_evap':           Tev,
                                    'T_cond':           Tcd,
                                    'superheat':        sh,
                                    'subcooling':       sc,
                                    'COP':              r['COP'],
                                    'eta_exergy':       r['eta_exergy'],
                                    'w_comp_kJ':        r['w_comp_kJ'],
                                    'q_evap_kJ':        r['q_evap_kJ'],
                                    'pressure_ratio':   r['pressure_ratio'],
                                    'ex_dest_comp':     r['ex_dest_comp_kJ'],
                                    'ex_dest_cond':     r['ex_dest_cond_kJ'],
                                    'ex_dest_evap':     r['ex_dest_evap_kJ'],
                                    'ex_dest_exp':      r['ex_dest_exp_kJ'],
                                    'ex_dest_total':    r['ex_dest_total_kJ'],
                                    'transcritical':    int(r['transcritical']),
                                })
                        except Exception:
                            pass

        print(f"  ✓ {ref} tamamlandı")

    df = pd.DataFrame(records)
    print(f"\n  Toplam veri noktası : {len(df)}")
    print(f"  Başarı oranı        : {len(df)/total*100:.1f}%")
    return df


def find_optimal_conditions(df):
    """
    Her akışkan için maksimum COP ve ekserji verimine sahip çalışma
    koşullarını belirle.
    """
    print(f"\n{'═'*70}")
    print("  OPTİMUM ÇALIŞMA KOŞULLARI")
    print(f"{'═'*70}")

    header = (f"{'Akışkan':<12} {'Opt_Tev':>8} {'Opt_Tcd':>8} "
              f"{'Max_COP':>9} {'η_ex@opt':>9}")
    print(header)
    print("─"*70)

    opt_results = {}
    for ref in REFRIGERANTS:
        sub = df[df['refrigerant'] == ref]
        if sub.empty:
            continue
        idx = sub['COP'].idxmax()
        row = sub.loc[idx]
        opt_results[ref] = {
            'T_evap':     row['T_evap'],
            'T_cond':     row['T_cond'],
            'max_COP':    row['COP'],
            'eta_exergy': row['eta_exergy'],
        }
        print(f"{ref:<12} {row['T_evap']:>8.0f} {row['T_cond']:>8.0f} "
              f"{row['COP']:>9.3f} {row['eta_exergy']:>9.3f}")

    return opt_results


def quick_analysis(refrigerant, T_evap_C, T_cond_C,
                   superheat=7, subcooling=5, eta_isentropic=0.85):
    """
    Tek bir akışkan için hızlı analiz.
    Örnek: quick_analysis('R290', -10, 40)
    """
    r = vapor_compression_cycle(refrigerant, T_evap_C, T_cond_C,
                                superheat=superheat, subcooling=subcooling,
                                eta_isentropic=eta_isentropic)
    print(f"\n{'─'*50}")
    print(f"  {refrigerant} | Tev={T_evap_C}°C | Tcond={T_cond_C}°C")
    print(f"{'─'*50}")
    print(f"  COP                : {r['COP']:.4f}")
    print(f"  Ekserji Verimi     : {r['eta_exergy']*100:.2f}%")
    print(f"  Soğutma Etkisi     : {r['q_evap_kJ']:.2f} kJ/kg")
    print(f"  Kompresör İşi      : {r['w_comp_kJ']:.2f} kJ/kg")
    print(f"  P_evap / P_cond    : {r['P_evap_kPa']:.1f} / {r['P_cond_kPa']:.1f} kPa")
    print(f"  Basınç Oranı       : {r['pressure_ratio']:.2f}")
    print(f"  Transkritik        : {'EVET' if r['transcritical'] else 'HAYIR'}")
    print(f"\n  Ekserji Yıkımları:")
    print(f"    Kompresör        : {r['ex_dest_comp_kJ']:.4f} kJ/kg")
    print(f"    Kondenser        : {r['ex_dest_cond_kJ']:.4f} kJ/kg")
    print(f"    Evaporatör       : {r['ex_dest_evap_kJ']:.4f} kJ/kg")
    print(f"    Genleşme Valfi   : {r['ex_dest_exp_kJ']:.4f} kJ/kg")
    print(f"    TOPLAM           : {r['ex_dest_total_kJ']:.4f} kJ/kg")
    return r
