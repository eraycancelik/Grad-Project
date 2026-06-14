import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from src.config import REFRIGERANTS, GWP
from src.thermodynamics import vapor_compression_cycle

def plot_cop_vs_tevap(df, T_cond_C=45, save_path=None):
    """COP vs Evaporasyon Sıcaklığı (Makale 1, Şekil 8a'ya benzer)"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'COP ve Ekserji Verimi vs Evaporasyon Sıcaklığı\n'
                 f'(Tcond = {T_cond_C}°C, ΔTsup = 7°C, ΔTsub = 5°C)',
                 fontsize=13, fontweight='bold')

    sub = df[(df['T_cond'] == T_cond_C) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    for ref, props in REFRIGERANTS.items():
        d = sub[sub['refrigerant'] == ref].sort_values('T_evap')
        if d.empty:
            continue
        axes[0].plot(d['T_evap'], d['COP'],
                     color=props['color'], marker=props['marker'],
                     label=props['label'], linewidth=2, markersize=6)
        axes[1].plot(d['T_evap'], d['eta_exergy'] * 100,
                     color=props['color'], marker=props['marker'],
                     label=props['label'], linewidth=2, markersize=6)

    axes[0].set_xlabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    axes[0].set_ylabel('COP [-]', fontsize=11)
    axes[0].set_title('Performans Katsayısı (COP)', fontsize=11)
    axes[0].legend(fontsize=9)

    axes[1].set_xlabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    axes[1].set_ylabel('Ekserji Verimi [%]', fontsize=11)
    axes[1].set_title('Ekserji Verimi (η_ex)', fontsize=11)
    axes[1].legend(fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()


def plot_exergy_destruction(ref_results, T_evap_C=-3, T_cond_C=45, save_path=None):
    """Bileşen bazında ekserji yıkımı çubuk grafik (Makale 1, Şekil 10)"""
    components   = ['Kompresör', 'Kondenser', 'Evaporatör', 'Genleşme']
    comp_keys    = ['ex_dest_comp_kJ', 'ex_dest_cond_kJ',
                    'ex_dest_evap_kJ', 'ex_dest_exp_kJ']
    comp_colors  = ['#E53935', '#FB8C00', '#43A047', '#1E88E5']

    refs  = list(ref_results.keys())
    x     = np.arange(len(refs))
    width = 0.18

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(
        f'Bileşen Bazında Ekserji Yıkımı\n'
        f'Tev = {T_evap_C}°C | Tcond = {T_cond_C}°C',
        fontsize=13, fontweight='bold')

    for i, (comp, key, color) in enumerate(zip(components, comp_keys, comp_colors)):
        vals = [abs(ref_results[r].get(key, 0)) for r in refs]
        ax.bar(x + (i - 1.5) * width, vals, width,
               label=comp, color=color, alpha=0.85, edgecolor='white')

    ax.set_xlabel('Soğutucu Akışkan', fontsize=11)
    ax.set_ylabel('Ekserji Yıkımı [kJ/kg]', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([REFRIGERANTS[r]['label'] for r in refs],
                       rotation=15, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()


def plot_ml_results(ml_results, target, save_path=None):
    """ML model karşılaştırması: Gerçek vs Tahmin + R² barları"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f'Makine Öğrenmesi Sonuçları — Hedef: {target}',
                 fontsize=13, fontweight='bold')

    model_names = list(ml_results.keys())
    colors_ml   = ['#2196F3', '#4CAF50', '#FF9800']

    for ax, (name, res), color in zip(axes, ml_results.items(), colors_ml):
        yt = res['y_test']
        yp = res['y_pred']
        ax.scatter(yt, yp, alpha=0.4, s=15, color=color, label='Tahminler')

        mn, mx = min(yt.min(), yp.min()), max(yt.max(), yp.max())
        ax.plot([mn, mx], [mn, mx], 'k--', linewidth=1.5, label='İdeal')

        ax.set_xlabel(f'Gerçek {target}', fontsize=10)
        ax.set_ylabel(f'Tahmin {target}', fontsize=10)
        ax.set_title(f'{name}\nR²={res["r2"]:.4f} | MAE={res["mae"]:.4f}',
                     fontsize=10)
        ax.legend(fontsize=8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()


def plot_cop_heatmap(df, refrigerant='R290', save_path=None):
    """COP ısı haritası: Tev vs Tcond (belirli bir akışkan için)"""
    sub = df[(df['refrigerant'] == refrigerant) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    pivot = sub.pivot_table(values='COP', index='T_evap', columns='T_cond')

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.values, aspect='auto', origin='lower',
                   cmap='RdYlGn', interpolation='bilinear')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f'{c:.0f}' for c in pivot.columns], fontsize=9)
    ax.set_yticklabels([f'{i:.0f}' for i in pivot.index], fontsize=9)

    ax.set_xlabel('Kondensasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_ylabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — COP Isı Haritası',
                 fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COP [-]', fontsize=10)

    # Değerleri hücrelere yaz
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color='black')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()

def plot_cop_heatmap2(df, refrigerant='R1234yf', save_path=None):
    """COP ısı haritası: Tev vs Tcond (belirli bir akışkan için)"""
    sub = df[(df['refrigerant'] == refrigerant) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    pivot = sub.pivot_table(values='COP', index='T_evap', columns='T_cond')

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.values, aspect='auto', origin='lower',
                   cmap='RdYlGn', interpolation='bilinear')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f'{c:.0f}' for c in pivot.columns], fontsize=9)
    ax.set_yticklabels([f'{i:.0f}' for i in pivot.index], fontsize=9)

    ax.set_xlabel('Kondensasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_ylabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — COP Isı Haritası',
                 fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COP [-]', fontsize=10)

    # Değerleri hücrelere yaz
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color='black')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()

def plot_cop_heatmap3(df, refrigerant='R744', save_path=None):
    """COP ısı haritası: Tev vs Tcond (belirli bir akışkan için)"""
    sub = df[(df['refrigerant'] == refrigerant) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    pivot = sub.pivot_table(values='COP', index='T_evap', columns='T_cond')

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.values, aspect='auto', origin='lower',
                   cmap='RdYlGn', interpolation='bilinear')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f'{c:.0f}' for c in pivot.columns], fontsize=9)
    ax.set_yticklabels([f'{i:.0f}' for i in pivot.index], fontsize=9)

    ax.set_xlabel('Kondensasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_ylabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — COP Isı Haritası',
                 fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COP [-]', fontsize=10)

    # Değerleri hücrelere yaz
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color='black')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()

def plot_cop_heatmap4(df, refrigerant='R600a', save_path=None):
    """COP ısı haritası: Tev vs Tcond (belirli bir akışkan için)"""
    sub = df[(df['refrigerant'] == refrigerant) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    pivot = sub.pivot_table(values='COP', index='T_evap', columns='T_cond')

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.values, aspect='auto', origin='lower',
                   cmap='RdYlGn', interpolation='bilinear')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f'{c:.0f}' for c in pivot.columns], fontsize=9)
    ax.set_yticklabels([f'{i:.0f}' for i in pivot.index], fontsize=9)

    ax.set_xlabel('Kondensasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_ylabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — COP Isı Haritası',
                 fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COP [-]', fontsize=10)

    # Değerleri hücrelere yaz
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color='black')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()


def plot_cop_heatmap5(df, refrigerant='R134a', save_path=None):
    """COP ısı haritası: Tev vs Tcond (belirli bir akışkan için)"""
    sub = df[(df['refrigerant'] == refrigerant) &
             (df['superheat'] == 7) &
             (df['subcooling'] == 5)]

    pivot = sub.pivot_table(values='COP', index='T_evap', columns='T_cond')

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.values, aspect='auto', origin='lower',
                   cmap='RdYlGn', interpolation='bilinear')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f'{c:.0f}' for c in pivot.columns], fontsize=9)
    ax.set_yticklabels([f'{i:.0f}' for i in pivot.index], fontsize=9)

    ax.set_xlabel('Kondensasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_ylabel('Evaporasyon Sıcaklığı [°C]', fontsize=11)
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — COP Isı Haritası',
                 fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COP [-]', fontsize=10)

    # Değerleri hücrelere yaz
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color='black')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()



def plot_gwp_cop_comparison(ref_results, save_path=None):
    """GWP vs COP baloncuk grafiği"""
    fig, ax = plt.subplots(figsize=(10, 6))

    for ref, props in REFRIGERANTS.items():
        if ref not in ref_results:
            continue
        cop  = ref_results[ref]['COP']
        etax = ref_results[ref]['eta_exergy']
        gwp  = GWP[ref]
        size = etax * 3000

        ax.scatter(gwp, cop, s=size, color=props['color'],
                   alpha=0.7, edgecolors='black', linewidth=1.5,
                   zorder=3, label=f"{props['label']}\n(GWP={gwp}, η_ex={etax:.2f})")
        ax.annotate(ref, (gwp, cop), textcoords='offset points',
                    xytext=(8, 8), fontsize=10, fontweight='bold',
                    color=props['color'])

    ax.set_xscale('log')
    ax.set_xlabel('GWP (100 yıl) — logaritmik ölçek', fontsize=11)
    ax.set_ylabel('COP [-]', fontsize=11)
    ax.set_title('COP vs GWP Karşılaştırması\n(Balon boyutu ∝ Ekserji Verimi)',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='upper right', framealpha=0.9)
    ax.axvline(x=150, color='red', linestyle='--', alpha=0.5,
               label='GWP=150 sınırı')
    ax.text(160, ax.get_ylim()[0] * 1.05, 'EU F-Gas\nsınırı',
            color='red', fontsize=8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()

    

def plot_ph_diagram(refrigerant, T_evap_C=-3, T_cond_C=45,
                    superheat=7, subcooling=5, save_path=None):
    """P-h diyagramı üzerinde çevrim görselleştirmesi"""
    r = vapor_compression_cycle(refrigerant, T_evap_C, T_cond_C,
                                superheat=superheat, subcooling=subcooling)

    T_crit = CP.PropsSI('Tcrit', refrigerant) - 273.15
    P_crit = CP.PropsSI('Pcrit', refrigerant) / 1e5   # bar

    # Doyma eğrisi
    T_sat = np.linspace(CP.PropsSI('Tmin', refrigerant) + 5,
                        CP.PropsSI('Tcrit', refrigerant) - 0.1, 200)
    h_liq, h_vap, P_sat = [], [], []
    for T in T_sat:
        try:
            h_liq.append(CP.PropsSI('H', 'T', T, 'Q', 0, refrigerant) / 1000)
            h_vap.append(CP.PropsSI('H', 'T', T, 'Q', 1, refrigerant) / 1000)
            P_sat.append(CP.PropsSI('P', 'T', T, 'Q', 0, refrigerant) / 1e5)
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(11, 7))
    color = REFRIGERANTS[refrigerant]['color']

    # Doyma eğrisi
    ax.plot(h_liq, P_sat, 'k-', linewidth=2, label='Doyma eğrisi')
    ax.plot(h_vap, P_sat, 'k-', linewidth=2)
    ax.scatter([CP.PropsSI('H', 'T', CP.PropsSI('Tcrit', refrigerant),
                            'Q', 0.5, refrigerant) / 1000],
               [P_crit], color='black', s=80, zorder=5, label='Kritik nokta')

    # Çevrim noktaları
    P_ev = r['P_evap_kPa'] / 100    # kPa → bar
    P_cd = r['P_cond_kPa'] / 100

    h_pts = [r['h1_kJ'], r['h2_kJ'], r['h3_kJ'], r['h4_kJ'], r['h1_kJ']]
    P_pts = [P_ev, P_cd, P_cd, P_ev, P_ev]
    labels = ['1', '2', '3', '4']

    ax.plot(h_pts, P_pts, color=color, linewidth=2.5, zorder=4)

    for i, (h, P, lbl) in enumerate(zip(h_pts[:4], P_pts[:4], labels)):
        ax.scatter(h, P, color=color, s=100, zorder=6, edgecolors='black')
        ax.annotate(f' {lbl}', (h, P), fontsize=12, fontweight='bold',
                    color=color, xytext=(5, 5), textcoords='offset points')

    # İzobar çizgileri
    ax.axhline(P_ev, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(P_cd, color='gray', linestyle=':', alpha=0.5)

    ax.set_xlabel('Entalpi h [kJ/kg]', fontsize=11)
    ax.set_ylabel('Basınç P [bar]', fontsize=11)
    ax.set_yscale('log')
    ax.set_title(f'{REFRIGERANTS[refrigerant]["label"]} — P-h Diyagramı\n'
                 f'Tev={T_evap_C}°C | Tcond={T_cond_C}°C | '
                 f'COP={r["COP"]:.3f}',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"  Grafik kaydedildi: {save_path}")
    plt.show()