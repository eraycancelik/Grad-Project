from src.thermodynamics import vapor_compression_cycle

def validate_model():
    """
    Modeli De Paula et al. (2020) Tablo 7 sonuçlarıyla karşılaştır.
    Referans koşullar: Tev = -3°C, Tcond = 45°C, Brazil (β = 0.082)
    """
    print("\n" + "═"*70)
    print("  DOĞRULAMA — De Paula et al. (2020), Tablo 7")
    print("  Koşullar: Tev = -3°C | Tcond = 45°C | ΔTsup = 7°C | ΔTsub = 5°C")
    print("═"*70)

    # Makaledeki referans değerler
    ref_values = {
        'R134a':   {'COP': 2.30, 'eta_exergy': 0.411},
        'R1234yf': {'COP': 1.98, 'eta_exergy': 0.356},
        'R290':    {'COP': 2.32, 'eta_exergy': 0.415},
        'R744':    {'COP': 2.19, 'eta_exergy': 0.398},
    }

    results = {}
    header = f"{'Akışkan':<12} {'COP_sim':>8} {'COP_ref':>8} {'Hata%':>7} "
    header += f"{'η_ex_sim':>9} {'η_ex_ref':>9} {'Hata%':>7}"
    print(header)
    print("─"*70)

    for ref in ['R134a', 'R1234yf', 'R290', 'R744']:
        r = vapor_compression_cycle(ref, -3, 45, superheat=7, subcooling=5,
                                    eta_isentropic=0.5)
        results[ref] = r

        ref_cop  = ref_values[ref]['COP']
        ref_etax = ref_values[ref]['eta_exergy']
        err_cop  = abs(r['COP'] - ref_cop)  / ref_cop  * 100
        err_etax = abs(r['eta_exergy'] - ref_etax) / ref_etax * 100

        print(f"{ref:<12} {r['COP']:>8.3f} {ref_cop:>8.3f} {err_cop:>6.1f}% "
              f"{r['eta_exergy']:>9.3f} {ref_etax:>9.3f} {err_etax:>6.1f}%")

    print("─"*70)
    print("  Not: Farklar; isentropik verim modeli ve gerçek kompresör")
    print("       verimliliği kullanımından kaynaklanmaktadır.")
    return results
