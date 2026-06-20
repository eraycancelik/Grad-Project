import os
from src.config import GWP

def print_summary_report(ref_results, ml_cop, ml_exergy, opt_results,
                         save_path='output/rapor.txt'):
    """Tüm analizlerin özet raporu — ekrana ve dosyaya yazar."""

    lines = []

    def w(text=''):
        """Hem ekrana yaz hem listeye ekle."""
        print(text)
        lines.append(text)

    # ── Başlık ──────────────────────────────────────────────────────────────
    w("\n" + "═"*70)
    w("  ÖZET RAPOR")
    w("═"*70)

    # ── [1] Termodinamik Sonuçlar ────────────────────────────────────────────
    w("\n  [1] Termodinamik Sonuçlar (Tev=-3°C, Tcond=45°C)")
    w(f"  {'Akışkan':<12} {'COP':>7} {'η_ex%':>7} {'GWP':>6} {'P_oran':>8}")
    w("  " + "─"*45)
    for ref, r in ref_results.items():
        w(f"  {ref:<12} {r['COP']:>7.3f} "
          f"{r['eta_exergy']*100:>6.1f}% {GWP[ref]:>6} "
          f"{r['pressure_ratio']:>8.2f}")

    best_cop_ref = max(ref_results, key=lambda x: ref_results[x]['COP'])
    best_ex_ref  = max(ref_results, key=lambda x: ref_results[x]['eta_exergy'])
    w(f"\n  ► En yüksek COP      : {best_cop_ref} ({ref_results[best_cop_ref]['COP']:.3f})")
    w(f"  ► En yüksek η_exerji : {best_ex_ref} ({ref_results[best_ex_ref]['eta_exergy']*100:.1f}%)")

    # ── [2] ML Model Performansı ─────────────────────────────────────────────
    w("\n  [2] ML Model Performansı")
    for target, ml_res in [('COP', ml_cop), ('eta_exergy', ml_exergy)]:
        best_name = max(ml_res, key=lambda x: ml_res[x]['r2'])
        r2  = ml_res[best_name]['r2']
        mae = ml_res[best_name]['mae']
        w(f"  {target:<15} → En iyi: {best_name:<20} R²={r2:.4f} MAE={mae:.4f}")

    # ── [3] Optimum Çalışma Noktaları ────────────────────────────────────────
    w("\n  [3] Optimum Çalışma Noktaları")
    for ref, opt in opt_results.items():
        w(f"  {ref:<12} Tev={opt['T_evap']:>5.0f}°C  "
          f"Tcond={opt['T_cond']:>5.0f}°C  "
          f"Max_COP={opt['max_COP']:.3f}")

    # ── Kapanış ──────────────────────────────────────────────────────────────
    w("\n" + "═"*70)
    w("  Analiz tamamlandı.")
    w("═"*70 + "\n")

    # ── Dosyaya yaz ──────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Rapor kaydedildi: {save_path}")