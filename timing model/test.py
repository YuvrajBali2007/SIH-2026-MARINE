import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

# 1. Load Data & Augment Synthetic Target Variables
df = pd.read_csv("freight_ship_fuel_sample_1000 (1).csv")
np.random.seed(42)

base_rate = (df['dwt'] * 0.4) - (df['vessel_age'] * 150) + (df['fuel_price'] * 10)
df['current_charter_rate'] = base_rate + np.random.normal(0, 3000, size=len(df))

trend = 1.01 
volatility_shock = np.where(df['wind_speed'] > 15, 2500, 0)
df['future_charter_rate_7d'] = (df['current_charter_rate'] * trend) + volatility_shock + np.random.normal(0, 2000, size=len(df))

features = ['dwt', 'engine_power', 'vessel_age', 'fuel_price', 'current_charter_rate', 'wind_speed']
X = df[features]
y = df['future_charter_rate_7d']

# 2. Chronological Split (Simulating real-world time passing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

# 3. Train Base Linear Regression
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)

# 4. Hyperparameter Tuning using GridSearchCV
print("Starting Grid Search... (this may take a few seconds)")

param_grid = {
    'n_estimators': [50, 100, 150],
    'learning_rate': [0.03, 0.05, 0.1],
    'max_depth': [3, 4, 5],
    'min_samples_split': [2, 5]
}

gbr = GradientBoostingRegressor(random_state=42)
grid_search = GridSearchCV(
    estimator=gbr,
    param_grid=param_grid,
    cv=3, # 3-fold cross validation
    scoring='neg_mean_absolute_error',
    n_jobs=-1 # Uses all available CPU cores
)

grid_search.fit(X_train, y_train)

print(f"Best Model Parameters Found: {grid_search.best_params_}\n")

# 5. Extract the Best Model & Generate Predictions
best_tree_model = grid_search.best_estimator_

lr_preds = lr_model.predict(X_test)
tree_preds = best_tree_model.predict(X_test)

# 6. Create the 70/30 Ensemble 
ensemble_preds = (0.7 * tree_preds) + (0.3 * lr_preds)

# 7. Business Evaluation Harness
def evaluate_timing_model(y_actual, current_rates, y_pred, wait_penalty=5000):
    # Forecasting Metrics
    mae = mean_absolute_error(y_actual, y_pred)
    rmse = root_mean_squared_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)
    
    # Directional Accuracy 
    actual_direction = (y_actual > current_rates).astype(int)
    predicted_direction = (y_pred > current_rates).astype(int)
    dir_acc = np.mean(actual_direction == predicted_direction) * 100

    # Decision Simulation
    predicted_cost_wait = y_pred + wait_penalty
    actual_cost_wait = y_actual + wait_penalty

    # Strategy Execution
    model_decision_book = (current_rates <= predicted_cost_wait)
    
    cost_always_now = current_rates.sum()
    cost_always_wait = actual_cost_wait.sum()
    cost_model = np.where(model_decision_book, current_rates, actual_cost_wait).sum()

    savings_vs_always_now = cost_always_now - cost_model
    savings_vs_always_wait = cost_always_wait - cost_model

    print("=" * 45)
    print("        MODEL EVALUATION & BACKTEST        ")
    print("=" * 45)
    print(f"MAE:                  ${mae:,.2f}")
    print(f"RMSE:                 ${rmse:,.2f}")
    print(f"R² Score:             {r2:.4f}")
    print(f"Directional Accuracy: {dir_acc:.2f}%\n")
    print("-" * 45)
    print("         BUSINESS POLICY BACKTEST         ")
    print("-" * 45)
    print(f"Cost (Always Book Now):  ${cost_always_now:,.2f}")
    print(f"Cost (Always Wait):      ${cost_always_wait:,.2f}")
    print(f"Cost (Model Strategy):   ${cost_model:,.2f}\n")
    print(f"Net Savings vs Always Now:  ${savings_vs_always_now:,.2f}")
    print(f"Net Savings vs Always Wait: ${savings_vs_always_wait:,.2f}")
    print("=" * 45)

evaluate_timing_model(
    y_actual=y_test,
    current_rates=X_test['current_charter_rate'],
    y_pred=ensemble_preds,
    wait_penalty=5000
)