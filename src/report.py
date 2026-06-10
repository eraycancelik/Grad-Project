from src.config import GWP

def print_summary_report(ref_results, ml_cop, ml_exergy, opt_results):
    """Tüm analizlerin özet raporu"""
    print("\n" + "═"*70)
    print("  ÖZET RAPOR")
    print("═"*70)

    print("\n  [1] Termodinamik Sonuçlar (Tev=-3°C, Tcond=45°C)")
    print(f"  {'Akışkan':<12} {'COP':>7} {'η_ex%':>7} {'GWP':>6} "
          f"{'P_oran':>8}")
    print("  " + "─"*45)
    for ref, r in ref_results.items():
        print(f"  {ref:<12} {r['COP']:>7.3f} "
              f"{r['eta_exergy']*100:>6.1f}% {GWP[ref]:>6} "
              f"{r['pressure_ratio']:>8.2f}")

    best_cop_ref = max(ref_results, key=lambda x: ref_results[x]['COP'])
    best_ex_ref  = max(ref_results, key=lambda x: ref_results[x]['eta_exergy'])
    print(f"\n  ► En yüksek COP      : {best_cop_ref} ({ref_results[best_cop_ref]['COP']:.3f})")
    print(f"  ► En yüksek η_exerji : {best_ex_ref} ({ref_results[best_ex_ref]['eta_exergy']*100:.1f}%)")

    print("\n  [2] ML Model Performansı")
    for target, ml_res in [('COP', ml_cop), ('eta_exergy', ml_exergy)]:
        best_name = max(ml_res, key=lambda x: ml_res[x]['r2'])
        r2  = ml_res[best_name]['r2']
        mae = ml_res[best_name]['mae']
        print(f"  {target:<15} → En iyi: {best_name:<20} R²={r2:.4f} MAE={mae:.4f}")

    print("\n  [3] Optimum Çalışma Noktaları")
    for ref, opt in opt_results.items():
        print(f"  {ref:<12} Tev={opt['T_evap']:>5.0f}°C  "
              f"Tcond={opt['T_cond']:>5.0f}°C  "
              f"Max_COP={opt['max_COP']:.3f}")

    print("\n" + "═"*70)
    print("  Analiz tamamlandı.")
    print("═"*70 + "\n")
