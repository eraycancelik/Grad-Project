import os
import warnings
import numpy as np

from src.config import setup_matplotlib_config
from src.validation import validate_model
from src.analysis import compare_refrigerants, parametric_scan, find_optimal_conditions
from src.visualization import (plot_ph_diagram, plot_gwp_cop_comparison, 
                           plot_exergy_destruction, plot_cop_vs_tevap, 
                           plot_cop_heatmap, plot_cop_heatmap2, plot_cop_heatmap3, 
                           plot_cop_heatmap4, plot_cop_heatmap5, plot_ml_results)
from src.ml_models import train_ml_models, feature_importance_analysis
from src.report import print_summary_report

def main():
    print("\n" + "█"*70)
    print("  SOĞUTUCU AKIŞKAN ANALİZİ — Python + CoolProp")
    print("  R134a | R290 | R1234yf | R744(CO₂) | R600a")
    print("█"*70)

    # ── A. Model doğrulama ──────────────────────────────────────────────────
    validate_model()

    # ── B. Karşılaştırmalı analiz (referans nokta) ──────────────────────────
    ref_results = compare_refrigerants(T_evap_C=-3, T_cond_C=45)

    # Output klasörünü oluştur
    os.makedirs('output', exist_ok=True)

    # ── C. P-h diyagramları ─────────────────────────────────────────────────
    print("\n  P-h Diyagramları çiziliyor...")
    for ref in ['R134a', 'R290', 'R744']:
        plot_ph_diagram(ref, T_evap_C=-3, T_cond_C=45,
                        save_path=f'output/ph_{ref}.png')

    # ── D. GWP vs COP baloncuk grafiği ─────────────────────────────────────
    plot_gwp_cop_comparison(ref_results,
                            save_path='output/gwp_cop.png')

    # ── E. Ekserji yıkımı grafiği ───────────────────────────────────────────
    plot_exergy_destruction(ref_results, T_evap_C=-3, T_cond_C=45,
                            save_path='output/exergy_destruction.png')

    # ── F. Parametrik tarama (ML veri seti) ─────────────────────────────────
    print("\n  Parametrik tarama başlıyor (bu biraz zaman alabilir)...")
    df = parametric_scan(
        T_evap_range   = np.arange(-30, 6, 5),
        T_cond_range   = np.arange(30, 56, 5),
        superheat_range  = [3, 5, 7, 10],
        subcooling_range = [3, 5, 7],
    )

    # Veri setini kaydet
    df.to_csv('output/refrigerant_dataset.csv', index=False)
    print(f"  Veri seti kaydedildi: output/refrigerant_dataset.csv ({len(df)} satır)")

    # ── G. COP vs Tev grafikleri ─────────────────────────────────────────────
    plot_cop_vs_tevap(df, T_cond_C=45,
                      save_path='output/cop_vs_tevap.png')

    # ── H. COP ısı haritası (R290) ──────────────────────────────────────────
    plot_cop_heatmap(df, refrigerant='R290',
                     save_path='output/cop_heatmap_R290.png')
    
    plot_cop_heatmap2(df, refrigerant='R1234yf',
                     save_path='output/cop_heatmap_R1234yf.png')

    plot_cop_heatmap3(df, refrigerant='R744',
                     save_path='output/cop_heatmap_R744.png')

    plot_cop_heatmap4(df, refrigerant='R600a',
                     save_path='output/cop_heatmap_R600a.png')

    plot_cop_heatmap5(df, refrigerant='R134a',
                     save_path='output/cop_heatmap_R134a.png')

    # ── I. Makine Öğrenmesi — COP tahmini ───────────────────────────────────
    print("\n  COP için ML modelleri eğitiliyor...")
    ml_cop, feat_cols, scaler_cop, best_cop = train_ml_models(df, target='COP')
    feature_importance_analysis(ml_cop, feat_cols, 'COP')
    plot_ml_results(ml_cop, target='COP',
                    save_path='output/ml_cop_results.png')

    # ── J. Makine Öğrenmesi — Ekserji verimi tahmini ────────────────────────
    print("\n  Ekserji verimi için ML modelleri eğitiliyor...")
    ml_exergy, _, _, best_ex = train_ml_models(df, target='eta_exergy')
    plot_ml_results(ml_exergy, target='eta_exergy',
                    save_path='output/ml_exergy_results.png')

    # ── K. Optimizasyon ──────────────────────────────────────────────────────
    opt_results = find_optimal_conditions(df)

    # ── L. Özet rapor ────────────────────────────────────────────────────────
    print_summary_report(ref_results, ml_cop, ml_exergy, opt_results)

    return df, ref_results, ml_cop, ml_exergy, opt_results


if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    setup_matplotlib_config()
    df, ref_results, ml_cop, ml_exergy, opt_results = main()
