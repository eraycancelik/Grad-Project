import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
import CoolProp.CoolProp as CP
from src.config import REFRIGERANTS, GWP
from src.thermodynamics import vapor_compression_cycle

# ─────────────────────────────────────────────────────────────
#  GLOBAL STYLE
# ─────────────────────────────────────────────────────────────
STYLE = {
    "bg":         "#F8F9FB",
    "panel":      "#FFFFFF",
    "grid":       "#E4E8EE",
    "text":       "#1A2035",
    "subtext":    "#5A6478",
    "font_title":  13,
    "font_label":  10.5,
    "font_tick":    9,
    "font_annot":   9,
}

def _apply_base_style(fig, axes_list):
    fig.patch.set_facecolor(STYLE["bg"])
    for ax in axes_list:
        ax.set_facecolor(STYLE["panel"])
        ax.grid(True, color=STYLE["grid"], linewidth=0.8, linestyle="-", zorder=0)
        ax.tick_params(colors=STYLE["text"], labelsize=STYLE["font_tick"])
        for spine in ax.spines.values():
            spine.set_edgecolor("#D0D6E2")
            spine.set_linewidth(0.8)

def _suptitle(fig, text):
    """suptitle'ı içeride tutan güvenli yöntem — y=1.01 kırpma sorununu önler."""
    fig.suptitle(text, fontsize=STYLE["font_title"], fontweight="bold",
                 color=STYLE["text"])
    fig.tight_layout(rect=[0, 0, 1, 0.93])   # üstte %7 boşluk bırak

def _title(ax, text, pad=10):
    ax.set_title(text, fontsize=STYLE["font_title"], fontweight="bold",
                 color=STYLE["text"], pad=pad)

def _labels(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel, fontsize=STYLE["font_label"], color=STYLE["subtext"], labelpad=6)
    ax.set_ylabel(ylabel, fontsize=STYLE["font_label"], color=STYLE["subtext"], labelpad=6)

def _legend(ax, **kw):
    leg = ax.legend(fontsize=STYLE["font_annot"], framealpha=0.92,
                    edgecolor="#D0D6E2", facecolor=STYLE["panel"],
                    labelcolor=STYLE["text"], **kw)
    leg.get_frame().set_linewidth(0.8)
    return leg

def _savefig(fig, save_path):
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=150,
                    facecolor=fig.get_facecolor())
        print(f"  Kaydedildi: {save_path}")


# ─────────────────────────────────────────────────────────────
#  1. COP vs Evaporasyon Sıcaklığı
# ─────────────────────────────────────────────────────────────
def plot_cop_vs_tevap(df, T_cond_C=45, save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    _apply_base_style(fig, axes)

    sub = df[
        (df["T_cond"] == T_cond_C) &
        (df["superheat"] == 7) &
        (df["subcooling"] == 5)
    ]
    for ref, props in REFRIGERANTS.items():
        d = sub[sub["refrigerant"] == ref].sort_values("T_evap")
        if d.empty:
            continue
        kw = dict(color=props["color"], marker=props["marker"],
                  label=props["label"], linewidth=2, markersize=6,
                  markeredgecolor="white", markeredgewidth=0.8, zorder=3)
        axes[0].plot(d["T_evap"], d["COP"], **kw)
        axes[1].plot(d["T_evap"], d["eta_exergy"] * 100, **kw)

    _title(axes[0], "Performans Katsayısı (COP)")
    _labels(axes[0], "Evaporasyon Sıcaklığı [°C]", "COP [–]")
    _legend(axes[0], loc="upper left")

    _title(axes[1], "Ekserji Verimi (η_ex)")
    _labels(axes[1], "Evaporasyon Sıcaklığı [°C]", "Ekserji Verimi [%]")
    _legend(axes[1], loc="upper left")

    _suptitle(fig,
        f"COP ve Ekserji Verimi — Evaporasyon Sıcaklığı\n"
        f"Tcond = {T_cond_C}°C  |  ΔTsup = 7°C  |  ΔTsub = 5°C")
    _savefig(fig, save_path)
    plt.show()


# ─────────────────────────────────────────────────────────────
#  2. Ekserji Yıkımı
# ─────────────────────────────────────────────────────────────
def plot_exergy_destruction(ref_results, T_evap_C=-3, T_cond_C=45, save_path=None):
    components  = ["Kompresör", "Kondenser", "Evaporatör", "Genleşme"]
    comp_keys   = ["ex_dest_comp_kJ", "ex_dest_cond_kJ",
                   "ex_dest_evap_kJ", "ex_dest_exp_kJ"]
    comp_colors = ["#E53935", "#FB8C00", "#43A047", "#1E88E5"]

    refs  = list(ref_results.keys())
    x     = np.arange(len(refs))
    width = 0.19

    fig, ax = plt.subplots(figsize=(12, 5.5))
    _apply_base_style(fig, [ax])

    for i, (comp, key, color) in enumerate(zip(components, comp_keys, comp_colors)):
        vals = [abs(ref_results[r].get(key, 0)) for r in refs]
        bars = ax.bar(
            x + (i - 1.5) * width, vals, width,
            label=comp, color=color, alpha=0.88,
            edgecolor="white", linewidth=0.6, zorder=3,
        )
        for bar, v in zip(bars, vals):
            if v > 0.5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{v:.1f}", ha="center", va="bottom",
                    fontsize=7, color=STYLE["subtext"],
                )

    _labels(ax, "Soğutucu Akışkan", "Ekserji Yıkımı [kJ/kg]")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [REFRIGERANTS[r]["label"] for r in refs],
        fontsize=STYLE["font_tick"], color=STYLE["text"],
    )
    _legend(ax, loc="upper right", ncol=2)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.18)

    _suptitle(fig,
        f"Bileşen Bazında Ekserji Yıkımı\n"
        f"Tev = {T_evap_C}°C  |  Tcond = {T_cond_C}°C")
    _savefig(fig, save_path)
    plt.show()


# ─────────────────────────────────────────────────────────────
#  3. ML Sonuçları
# ─────────────────────────────────────────────────────────────
def plot_ml_results(ml_results, target, save_path=None):
    colors_ml = ["#2196F3", "#4CAF50", "#FF9800"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    _apply_base_style(fig, axes)

    for ax, (name, res), color in zip(axes, ml_results.items(), colors_ml):
        yt, yp = res["y_test"], res["y_pred"]
        ax.scatter(yt, yp, alpha=0.45, s=14, color=color,
                   label="Tahminler", zorder=3, edgecolors="none")
        mn, mx = min(yt.min(), yp.min()), max(yt.max(), yp.max())
        ax.plot([mn, mx], [mn, mx], "k--", linewidth=1.4, label="İdeal", zorder=4)
        _title(ax, f"{name}\nR² = {res['r2']:.4f}  |  MAE = {res['mae']:.4f}", pad=8)
        _labels(ax, f"Gerçek {target}", f"Tahmin {target}")
        _legend(ax, loc="upper left", markerscale=1.4)

    _suptitle(fig, f"Makine Öğrenmesi Sonuçları — Hedef: {target}")
    _savefig(fig, save_path)
    plt.show()


# ─────────────────────────────────────────────────────────────
#  4. COP Isı Haritası
# ─────────────────────────────────────────────────────────────
_COP_CMAP = LinearSegmentedColormap.from_list(
    "cop", ["#C62828", "#EF6C00", "#F9A825", "#AED581", "#2E7D32"], N=256
)

def _plot_cop_heatmap_base(df, refrigerant, vmin=None, vmax=None, save_path=None):
    sub = df[
        (df["refrigerant"] == refrigerant) &
        (df["superheat"] == 7) &
        (df["subcooling"] == 5)
    ]
    pivot = sub.pivot_table(values="COP", index="T_evap", columns="T_cond")

    fig, ax = plt.subplots(figsize=(10, 6.5))
    _apply_base_style(fig, [ax])

    im = ax.imshow(
        pivot.values, aspect="auto", origin="lower",
        cmap=_COP_CMAP, interpolation="bilinear",
        vmin=vmin or pivot.values.min(),
        vmax=vmax or pivot.values.max(),
    )
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels([f"{c:.0f}" for c in pivot.columns],
                       fontsize=STYLE["font_tick"], color=STYLE["text"])
    ax.set_yticklabels([f"{i:.0f}" for i in pivot.index],
                       fontsize=STYLE["font_tick"], color=STYLE["text"])

    _labels(ax, "Kondensasyon Sıcaklığı [°C]", "Evaporasyon Sıcaklığı [°C]")
    _title(ax, f"{REFRIGERANTS[refrigerant]['label']} — COP Isı Haritası")

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("COP [–]", fontsize=STYLE["font_label"], color=STYLE["subtext"])
    cbar.ax.tick_params(labelsize=STYLE["font_tick"], colors=STYLE["text"])
    cbar.outline.set_edgecolor("#D0D6E2")

    norm_vals = (pivot.values - im.norm.vmin) / (im.norm.vmax - im.norm.vmin)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if np.isnan(val):
                continue
            txt_color = "white" if norm_vals[i, j] < 0.35 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7.5, color=txt_color, fontweight="bold")

    fig.tight_layout()
    _savefig(fig, save_path)
    plt.show()


def plot_cop_heatmap (df, refrigerant="R290",    vmin=None, vmax=None, save_path=None):
    _plot_cop_heatmap_base(df, refrigerant, vmin, vmax, save_path)
def plot_cop_heatmap2(df, refrigerant="R1234yf", vmin=None, vmax=None, save_path=None):
    _plot_cop_heatmap_base(df, refrigerant, vmin, vmax, save_path)
def plot_cop_heatmap3(df, refrigerant="R744",    vmin=None, vmax=None, save_path=None):
    _plot_cop_heatmap_base(df, refrigerant, vmin, vmax, save_path)
def plot_cop_heatmap4(df, refrigerant="R600a",   vmin=None, vmax=None, save_path=None):
    _plot_cop_heatmap_base(df, refrigerant, vmin, vmax, save_path)
def plot_cop_heatmap5(df, refrigerant="R134a",   vmin=None, vmax=None, save_path=None):
    _plot_cop_heatmap_base(df, refrigerant, vmin, vmax, save_path)


# ─────────────────────────────────────────────────────────────
#  5. GWP vs COP
# ─────────────────────────────────────────────────────────────

# Sabit etiket offsetleri — üst üste binme önlemek için her akışkana özel
_GWP_LABEL_OFFSETS = {
    "R134a":   ( 15,  8),
    "R290":    ( 15, -18),
    "R1234yf": ( 15,  8),
    "R744":    ( 15,  8),
    "R600a":   ( 15,  8),
}

def plot_gwp_cop_comparison(ref_results, save_path=None):
    fig, ax = plt.subplots(figsize=(11, 6.2))
    _apply_base_style(fig, [ax])
    ax.grid(True, which="minor", color=STYLE["grid"], linewidth=0.4,
            linestyle=":", zorder=0)

    handles = []
    for ref, props in REFRIGERANTS.items():
        if ref not in ref_results:
            continue
        cop  = ref_results[ref]["COP"]
        etax = ref_results[ref]["eta_exergy"]
        gwp  = GWP[ref]
        size = etax * 1600

        ax.scatter(gwp, cop, s=size, color=props["color"], alpha=0.80,
                   edgecolors="white", linewidth=2.0, zorder=4)

        handles.append(mpatches.Patch(
            color=props["color"],
            label=f"{props['label']}   GWP={gwp}   η={etax:.2f}",
        ))

        dx, dy = _GWP_LABEL_OFFSETS.get(ref, (15, 8))
        ax.annotate(
            ref,
            xy=(gwp, cop),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=9.5, fontweight="bold", color=props["color"],
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
            arrowprops=dict(arrowstyle="-", color=props["color"],
                            lw=0.7, alpha=0.45),
            zorder=6,
        )

    # EU F-Gas sınırı
    ylims = ax.get_ylim()
    ax.axvline(x=150, color="#C62828", linestyle="--", linewidth=1.1,
               alpha=0.55, zorder=3)
    ax.text(118, ylims[0] + (ylims[1] - ylims[0]) * 0.05,
            "EU F-Gas sınırı\n(GWP < 150)",
            color="#C62828", fontsize=7.5, ha="right", va="bottom",
            rotation=90, alpha=0.75)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda v, _: f"{int(v):,}" if v >= 1 else f"{v:.1f}"
    ))

    _labels(ax, "GWP (100 yıl) — logaritmik ölçek", "COP [–]")
    _title(ax, "COP vs GWP Karşılaştırması  (balon boyutu ∝ ekserji verimi)")

    # Legend grafiğin tamamen dışında — sağ kenar
    leg = ax.legend(
        handles=handles,
        fontsize=8.5,
        framealpha=0.95,
        edgecolor="#D0D6E2",
        facecolor=STYLE["panel"],
        labelcolor=STYLE["text"],
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0,
        title="Akışkan",
        title_fontsize=9,
    )
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    fig.subplots_adjust(right=0.70)   # legend alanı
    _savefig(fig, save_path)
    plt.show()


# ─────────────────────────────────────────────────────────────
#  6. P-h Diyagramı
# ─────────────────────────────────────────────────────────────
def plot_ph_diagram(refrigerant, T_evap_C=-3, T_cond_C=45,
                    superheat=7, subcooling=5, save_path=None):
    r = vapor_compression_cycle(
        refrigerant, T_evap_C, T_cond_C,
        superheat=superheat, subcooling=subcooling,
    )

    P_crit = CP.PropsSI("Pcrit", refrigerant) / 1e5

    # Doyma eğrisi — sadece pozitif basınç bölgesi
    T_min_K = CP.PropsSI("Tmin", refrigerant) + 5
    T_crit_K = CP.PropsSI("Tcrit", refrigerant) - 0.1
    T_sat = np.linspace(T_min_K, T_crit_K, 300)

    h_liq, h_vap, P_sat_bar = [], [], []
    for T in T_sat:
        try:
            P = CP.PropsSI("P", "T", T, "Q", 0, refrigerant) / 1e5
            if P <= 0:          # negatif/sıfır basınç → atla (propan gibi)
                continue
            h_liq.append(CP.PropsSI("H", "T", T, "Q", 0, refrigerant) / 1000)
            h_vap.append(CP.PropsSI("H", "T", T, "Q", 1, refrigerant) / 1000)
            P_sat_bar.append(P)
        except Exception:
            pass

    P_ev = r["P_evap_kPa"] / 100
    P_cd = r["P_cond_kPa"] / 100

    h_pts = [r["h1_kJ"], r["h2_kJ"], r["h3_kJ"], r["h4_kJ"], r["h1_kJ"]]
    P_pts = [P_ev, P_cd, P_cd, P_ev, P_ev]

    color = REFRIGERANTS[refrigerant]["color"]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    _apply_base_style(fig, [ax])

    # Doyma eğrisi
    ax.plot(h_liq, P_sat_bar, color="#2C2C2C", linewidth=1.8,
            label="Doyma eğrisi", zorder=3)
    ax.plot(h_vap, P_sat_bar, color="#2C2C2C", linewidth=1.8, zorder=3)

    # Kritik nokta
    h_crit = CP.PropsSI(
        "H", "T", CP.PropsSI("Tcrit", refrigerant), "Q", 0.5, refrigerant
    ) / 1000
    ax.scatter([h_crit], [P_crit], color="black", s=70,
               zorder=6, label="Kritik nokta")

    # Çevrim okları
    step_pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for i, j in step_pairs:
        ax.annotate(
            "",
            xy=(h_pts[j], P_pts[j]),
            xytext=(h_pts[i], P_pts[i]),
            arrowprops=dict(arrowstyle="-|>", color=color,
                            lw=2.2, mutation_scale=14),
            zorder=5,
        )

    # Nokta etiketleri
    offsets_pt = {"1": (6, -14), "2": (6, 6), "3": (-18, 6), "4": (6, -14)}
    labels_pts = ["1", "2", "3", "4"]
    for h, P, lbl in zip(h_pts[:4], P_pts[:4], labels_pts):
        ax.scatter(h, P, color=color, s=90, zorder=7,
                   edgecolors="white", linewidth=1.5)
        ax.annotate(
            lbl, (h, P),
            xytext=offsets_pt.get(lbl, (6, 6)),
            textcoords="offset points",
            fontsize=12, fontweight="bold", color=color,
            zorder=8,
        )

    # Log ölçek — önce ayarla, sonra basınç etiketlerini ekle
    ax.set_yscale("log")

    # Y ekseni sınırları: en küçük pozitif P değerinden biraz aşağısı
    p_min_data = min(min(P_sat_bar), P_ev) * 0.5
    p_max_data = max(max(P_sat_bar), P_cd) * 1.5
    ax.set_ylim(p_min_data, p_max_data)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda v, _: f"{v:.0f}" if v >= 1 else f"{v:.2f}"
    ))

    # Basınç referans çizgileri
    x_left = ax.get_xlim()[0]
    for P_ref, P_lbl in [(P_ev, f"{P_ev:.1f} bar"), (P_cd, f"{P_cd:.1f} bar")]:
        ax.axhline(P_ref, color="#BBBBBB", linestyle="--", linewidth=0.9, zorder=2)
        ax.text(x_left, P_ref * 1.03, P_lbl,
                fontsize=7.5, color=STYLE["subtext"], va="bottom")

    _labels(ax, "Entalpi h [kJ/kg]", "Basınç P [bar]")
    _title(ax,
        f"{REFRIGERANTS[refrigerant]['label']} — P-h Diyagramı\n"
        f"Tev = {T_evap_C}°C  |  Tcond = {T_cond_C}°C  |  COP = {r['COP']:.3f}"
    )
    _legend(ax, loc="lower right")

    fig.tight_layout()
    _savefig(fig, save_path)
    plt.show()