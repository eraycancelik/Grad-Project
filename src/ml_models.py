import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
# pyrefly: ignore [missing-import]
import xgboost as xgb
from src.config import REFRIGERANT_CODES

def encode_refrigerant(df):
    """Akışkan adını sayısal koda çevir."""
    df = df.copy()
    df['ref_code'] = df['refrigerant'].map(REFRIGERANT_CODES)
    return df

def train_ml_models(df, target='COP'):
    """
    COP veya ekserji verimi tahmini için ML modelleri eğit.
    Makale 4 (Yıldırım 2025) ve Makale 5 (Tue & An 2026)'ya göre.
    """
    print(f"\n{'═'*60}")
    print(f"  MAKİNE ÖĞRENMESİ — Hedef: {target}")
    print(f"{'═'*60}")

    df = encode_refrigerant(df)

    feature_cols = ['ref_code', 'T_evap', 'T_cond', 'superheat', 'subcooling']
    X = df[feature_cols].values
    y = df[target].values

    # %80 eğitim / %20 test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    models = {
        'Random Forest':   RandomForestRegressor(
                               n_estimators=200, max_depth=12,
                               random_state=42, n_jobs=-1),
        'XGBoost':         xgb.XGBRegressor(
                               n_estimators=300, max_depth=8,
                               learning_rate=0.05, subsample=0.8,
                               random_state=42, verbosity=0),
        'Gradient Boost':  GradientBoostingRegressor(
                               n_estimators=200, max_depth=6,
                               learning_rate=0.05, random_state=42),
    }

    results = {}
    print(f"\n  {'Model':<20} {'R²':>8} {'MAE':>10} {'RMSE':>10} {'CV_R²':>10}")
    print("  " + "─"*58)

    best_model = None
    best_r2    = -np.inf

    for name, model in models.items():
        # XGBoost ham feature kullanır (ölçekleme gerekmez)
        if 'XGB' in name:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
        else:
            model.fit(X_train_sc, y_train)
            y_pred = model.predict(X_test_sc)
            cv_scores = cross_val_score(
                model, scaler.transform(X), y, cv=5, scoring='r2')

        r2   = r2_score(y_test, y_pred)
        mae  = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        cv_r2 = cv_scores.mean()

        results[name] = {
            'model': model, 'scaler': scaler if 'XGB' not in name else None,
            'r2': r2, 'mae': mae, 'rmse': rmse, 'cv_r2': cv_r2,
            'y_test': y_test, 'y_pred': y_pred,
        }
        print(f"  {name:<20} {r2:>8.4f} {mae:>10.4f} {rmse:>10.4f} {cv_r2:>10.4f}")

        if r2 > best_r2:
            best_r2    = r2
            best_model = name

    print(f"\n  ✓ En iyi model: {best_model} (R² = {best_r2:.4f})")
    return results, feature_cols, scaler, best_model


def feature_importance_analysis(ml_results, feature_cols, target):
    """Feature importance — hangi parametre COP'u en çok etkiliyor?"""
    feature_names = ['Akışkan', 'T_evap', 'T_cond', 'Süper Isıtma', 'Alt Soğutma']
    print(f"\n  Özellik Önemi ({target} için):")
    print("  " + "─"*40)
    for name, res in ml_results.items():
        model = res['model']
        if hasattr(model, 'feature_importances_'):
            imps = model.feature_importances_
            print(f"\n  [{name}]")
            for feat, imp in sorted(zip(feature_names, imps),
                                    key=lambda x: -x[1]):
                bar = "█" * int(imp * 40)
                print(f"  {feat:<16} {imp:.3f} {bar}")
