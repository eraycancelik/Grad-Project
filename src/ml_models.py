"""
ml_models_v2.py  —  Düzeltilmiş ML eğitimi

Değişiklik: R744 (transkritik) ayrı model olarak eğitiliyor.
Sebep: R744 transkritik çevrimde çalışır, diğer 4 akışkandan
termodinamik olarak temelden farklıdır. Birlikte eğitildiğinde
çapraz doğrulama skoru (CV_R²) ciddi biçimde bozulmaktadır.

Çözüm: 
  - Subkritik model  : R134a, R290, R1234yf, R600a
  - Transkritik model: R744
Her iki model aynı hiperparametrelerle eğitilir.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

# ─────────────────────────────────────────────────────────────────────
# ENCODE
# ─────────────────────────────────────────────────────────────────────

def encode_refrigerant(df):
    df = df.copy()
    le = LabelEncoder()
    df['ref_code'] = le.fit_transform(df['refrigerant'])
    return df, le


# ─────────────────────────────────────────────────────────────────────
# ANA EĞİTİM FONKSİYONU
# ─────────────────────────────────────────────────────────────────────

def train_ml_models(df, target='COP'):
    """
    Subkritik (R134a/R290/R1234yf/R600a) ve transkritik (R744)
    akışkanlar için ayrı ML modelleri eğitir.

    Dönüş:
        results_sub  : subkritik modellerin sonuçları
        results_r744 : R744 modelinin sonuçları
        feature_cols : girdi özellikleri
        le           : LabelEncoder
    """
    print(f"\n{'═'*65}")
    print(f"  MAKİNE ÖĞRENMESİ — Hedef: {target}")
    print(f"  [Subkritik: R134a/R290/R1234yf/R600a | Transkritik: R744]")
    print(f"{'═'*65}")

    df, le = encode_refrigerant(df)

    # Veri ayrımı
    df_sub  = df[df['transcritical'] == 0].copy()
    df_r744 = df[df['transcritical'] == 1].copy()

    feature_cols = ['ref_code', 'T_evap', 'T_cond', 'superheat', 'subcooling']

    def _get_models():
        return {
            'Random Forest':  RandomForestRegressor(
                                  n_estimators=200, max_depth=12,
                                  random_state=42, n_jobs=-1),
            'XGBoost':        xgb.XGBRegressor(
                                  n_estimators=300, max_depth=8,
                                  learning_rate=0.05, subsample=0.8,
                                  random_state=42, verbosity=0),
            'Gradient Boost': GradientBoostingRegressor(
                                  n_estimators=200, max_depth=6,
                                  learning_rate=0.05, random_state=42),
        }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    def _train_group(data, label):
        X = data[feature_cols].values
        y = data[target].values
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=0.2, random_state=42)

        results = {}
        print(f"\n  [{label}]")
        print(f"  {'Model':<20} {'R²':>8} {'MAE':>10} {'RMSE':>10} {'CV_R²':>10}")
        print("  " + "─"*60)

        best_name, best_r2 = None, -np.inf

        for name, model in _get_models().items():
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            cv     = cross_val_score(model, X, y, cv=kf, scoring='r2')

            r2   = r2_score(y_te, y_pred)
            mae  = mean_absolute_error(y_te, y_pred)
            rmse = np.sqrt(mean_squared_error(y_te, y_pred))
            cv_r2 = cv.mean()

            results[name] = {
                'model': model, 'r2': r2, 'mae': mae,
                'rmse': rmse, 'cv_r2': cv_r2,
                'y_test': y_te, 'y_pred': y_pred,
                'feature_importances': (model.feature_importances_
                                        if hasattr(model, 'feature_importances_')
                                        else None),
            }
            print(f"  {name:<20} {r2:>8.4f} {mae:>10.4f} {rmse:>10.4f} {cv_r2:>10.4f}")

            if r2 > best_r2:
                best_r2, best_name = r2, name

        print(f"\n  ✓ En iyi model: {best_name} (R²={best_r2:.4f})")
        return results

    results_sub  = _train_group(df_sub,  "SUBKRİTİK — R134a / R290 / R1234yf / R600a")
    results_r744 = _train_group(df_r744, "TRANSKRİTİK — R744 (CO₂)")

    return results_sub, results_r744, feature_cols, le


# ─────────────────────────────────────────────────────────────────────
# ÖZELLİK ÖNEMİ
# ─────────────────────────────────────────────────────────────────────

def feature_importance_analysis(results_sub, results_r744,
                                  feature_cols, target):
    feature_names = ['Akışkan', 'T_evap', 'T_cond', 'Süper Isıtma', 'Alt Soğutma']

    print(f"\n  Özellik Önemi ({target} için):")
    print("  " + "─"*45)

    for group_label, results in [("Subkritik", results_sub),
                                   ("R744",      results_r744)]:
        print(f"\n  [{group_label}]")
        for name, res in results.items():
            if res['feature_importances'] is None:
                continue
            imps = res['feature_importances']
            print(f"\n    {name}:")
            for feat, imp in sorted(zip(feature_names, imps),
                                    key=lambda x: -x[1]):
                bar = "█" * int(imp * 40)
                print(f"    {feat:<16} {imp:.3f} {bar}")