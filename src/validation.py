from src.thermodynamics import vapor_compression_cycle

FLUIDS = ['R134a', 'R290', 'R1234yf', 'R744', 'R600a']

# Test koşulları — birden fazla nokta test etmek daha güvenilir
TEST_CONDITIONS = [
    {'T_evap_C': -3,  'T_cond_C': 45, 'superheat': 7, 'subcooling': 5},
    {'T_evap_C': -10, 'T_cond_C': 40, 'superheat': 5, 'subcooling': 3},
    {'T_evap_C':   5, 'T_cond_C': 50, 'superheat': 3, 'subcooling': 7},
]

TOLERANCE = 0.001  # %0.1 — yani binde 1 hata payı

def validate_model():
    print("\n" + "═"*70)
    print("  DOĞRULAMA — 1. Termodinamik Yasa (Enerji Dengesi)")
    print("  Kontrol: q_evap + w_comp = q_cond")
    print("═"*70)
    print(f"  {'Akışkan':<10} {'Koşul':<22} {'q_ev+w_cp':>10} {'q_cd':>10} {'Hata%':>8} {'Durum':>8}")
    print("  " + "─"*68)

    all_passed = True

    for fluid in FLUIDS:
        for cond in TEST_CONDITIONS:
            try:
                r = vapor_compression_cycle(
                    refrigerant=fluid,
                    T_evap_C=cond['T_evap_C'],
                    T_cond_C=cond['T_cond_C'],
                    superheat=cond['superheat'],
                    subcooling=cond['subcooling'],
                )

                q_evap  = r['q_evap_kJ']
                w_comp  = r['w_comp_kJ']
                q_cond  = r['q_cond_kJ']

                lhs     = q_evap + w_comp      # sol taraf
                error   = abs(lhs - q_cond) / q_cond  # bağıl hata

                passed  = error < TOLERANCE
                status  = "✓ GEÇTİ" if passed else "✗ BAŞARISIZ"
                if not passed:
                    all_passed = False

                koşul_str = f"Tev={cond['T_evap_C']:+3d} Tcd={cond['T_cond_C']:3d}"
                print(f"  {fluid:<10} {koşul_str:<22} {lhs:>10.4f} {q_cond:>10.4f} "
                      f"{error*100:>7.4f}% {status:>8}")

            except Exception as e:
                all_passed = False
                print(f"  {fluid:<10} HATA: {e}")

    print("  " + "─"*68)
    if all_passed:
        print("  ✓ Tüm testler geçti — model 1. Yasa ile tutarlı")
    else:
        print("  ✗ Bazı testler başarısız — thermodynamics.py'ı kontrol edin")
    print("═"*70)