import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
from datetime import datetime, timedelta

print("="*70)
print(" FinUnity Market Simulator v2.1 - Mean-Reverting Price Forecasting")
print("="*70)

# 1. Load the real historical data
file_path = '../data/prices/wfp_food_prices_khm.csv'
df = pd.read_csv(file_path)

# 2. Convert date column
df['date'] = pd.to_datetime(df['date'])

# 3. Filter for Rice in Battambang
rice_data = df[
    (df['commodity'].str.contains('Rice', case=False, na=False)) & 
    (df['admin1'].str.contains('Battambang', case=False, na=False))
].sort_values('date').reset_index(drop=True)

print(f"\n📊 Dataset Loaded: {len(rice_data)} records from {rice_data['date'].min().date()} to {rice_data['date'].max().date()}")

# 4. Calculate Historical Statistics
current_price = rice_data['usdprice'].iloc[-1]
historical_mean = rice_data['usdprice'].mean()
historical_std = rice_data['usdprice'].std()
historical_volatility = (historical_std / historical_mean) * 100

print(f"\n📈 Historical Analysis:")
print(f"   Current Price: ${current_price:.3f}/unit")
print(f"   Historical Mean: ${historical_mean:.3f}/unit")
print(f"   Historical Volatility: {historical_volatility:.1f}%")

# 5. MONTE CARLO SIMULATION with Mean Reversion
print("\n🎲 Running Monte Carlo Simulation with Mean Reversion (1000 scenarios)...")

# Parameters
n_simulations = 1000
n_days = 180  # 6 months forecast
starting_price = current_price

# Mean reversion parameters
speed_of_reversion = 0.01  # How quickly prices return to mean (1% per day)
long_term_mean = historical_mean  # Prices revert to historical mean
volatility = historical_std / np.sqrt(252)  # Daily volatility

# Storage for simulation results
simulated_prices = np.zeros((n_simulations, n_days + 1))
simulated_prices[:, 0] = starting_price

# Run simulations using Ornstein-Uhlenbeck process (mean-reverting)
np.random.seed(42)
for i in range(n_simulations):
    price_path = [starting_price]
    current_price_sim = starting_price
    
    for day in range(n_days):
        # Mean reversion: drift toward long-term mean
        drift = speed_of_reversion * (long_term_mean - current_price_sim)
        # Random shock
        shock = volatility * np.random.normal()
        # Update price
        current_price_sim = current_price_sim + drift + (current_price_sim * shock)
        # Ensure price doesn't go negative
        current_price_sim = max(0.01, current_price_sim)
        price_path.append(current_price_sim)
    
    simulated_prices[i, :] = price_path

# Extract final prices (after 180 days)
final_prices = simulated_prices[:, -1]

# Calculate statistics
predicted_mean = np.mean(final_prices)
predicted_median = np.median(final_prices)
predicted_std = np.std(final_prices)
confidence_interval_95 = np.percentile(final_prices, [2.5, 97.5])
confidence_interval_80 = np.percentile(final_prices, [10, 90])

print(f"\n🔮 6-Month Price Forecast:")
print(f"   Predicted Mean Price: ${predicted_mean:.3f}")
print(f"   Predicted Median Price: ${predicted_median:.3f}")
print(f"   95% Confidence Interval: ${confidence_interval_95[0]:.3f} - ${confidence_interval_95[1]:.3f}")
print(f"   80% Confidence Interval: ${confidence_interval_80[0]:.3f} - ${confidence_interval_80[1]:.3f}")

# 6. ROI CALCULATION FOR FARMER
print("\n💰 Loan Viability Analysis (Example: 2 hectares, $500 loan)")

# Assumptions for rice farming in Cambodia
hectares = 2.0
loan_amount = 500
expected_yield_kg_per_hectare = 3000  # Typical yield for rainfed rice
total_expected_yield = hectares * expected_yield_kg_per_hectare

# Calculate revenue scenarios
revenue_at_mean = total_expected_yield * predicted_mean
revenue_at_median = total_expected_yield * predicted_median
revenue_at_lower_bound = total_expected_yield * confidence_interval_95[0]

# Calculate ROI
roi_mean = ((revenue_at_mean - loan_amount) / loan_amount) * 100
roi_median = ((revenue_at_median - loan_amount) / loan_amount) * 100
roi_worst_case = ((revenue_at_lower_bound - loan_amount) / loan_amount) * 100

# Calculate probability of positive ROI using net revenue after operating costs
operating_cost_rate = 0.40  # 40% operating costs
net_revenue_scenarios = (final_prices * total_expected_yield) * (1 - operating_cost_rate)
positive_roi_probability = (
    np.sum(net_revenue_scenarios > loan_amount)
    / n_simulations
) * 100

if positive_roi_probability > 95 and loan_amount < (revenue_at_mean * 0.3):
    print("⚠️ ROI probability appears high. Consider testing with larger loan amounts or stress scenarios.")

print(f"   Expected Yield: {total_expected_yield:,.0f} kg")
print(f"   Revenue at Mean Price: ${revenue_at_mean:,.2f}")
print(f"   Revenue at Median Price: ${revenue_at_median:,.2f}")
print(f"   ROI at Mean Price: {roi_mean:.1f}%")
print(f"   ROI at Median Price: {roi_median:.1f}%")
print(f"   Worst Case ROI (2.5th percentile): {roi_worst_case:.1f}%")
print(f"   ✅ Probability of Positive ROI: {positive_roi_probability:.1f}%")

# 7. RISK ASSESSMENT
print("\n⚠️  Risk Assessment:")
if positive_roi_probability >= 80:
    risk_level = "LOW"
    recommendation = "APPROVE"
    print(f"   Risk Level: {risk_level} - High probability of loan repayment")
elif positive_roi_probability >= 60:
    risk_level = "MEDIUM"
    recommendation = "REVIEW"
    print(f"   Risk Level: {risk_level} - Moderate probability, requires human review")
else:
    risk_level = "HIGH"
    recommendation = "REJECT"
    print(f"   Risk Level: {risk_level} - Low probability of loan repayment")

print(f"   AI Recommendation: {recommendation}")

# 8. VISUALIZATION
print("\n📊 Generating visualizations...")

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('FinUnity Market Analysis: Rice Prices in Battambang', fontsize=16, fontweight='bold')

# Plot 1: Historical prices with recent trend
axes[0, 0].plot(rice_data['date'], rice_data['usdprice'], color='#2E8B57', linewidth=2)
axes[0, 0].axhline(y=current_price, color='red', linestyle='--', linewidth=1.5, label=f'Current: ${current_price:.3f}')
axes[0, 0].axhline(y=historical_mean, color='blue', linestyle=':', linewidth=1.5, label=f'Mean: ${historical_mean:.3f}')
axes[0, 0].set_title('Historical Rice Prices', fontweight='bold')
axes[0, 0].set_xlabel('Year')
axes[0, 0].set_ylabel('Price (USD)')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Monte Carlo simulation paths (sample of 100)
sample_sims = np.random.choice(n_simulations, 100, replace=False)
for i in sample_sims:
    days = np.arange(n_days + 1)
    axes[0, 1].plot(days, simulated_prices[i], alpha=0.1, color='blue')

# Plot mean and confidence intervals
axes[0, 1].plot(days, np.mean(simulated_prices, axis=0), color='red', linewidth=2.5, label='Mean Forecast')
axes[0, 1].fill_between(days, 
                         np.percentile(simulated_prices, 2.5, axis=0),
                         np.percentile(simulated_prices, 97.5, axis=0),
                         alpha=0.3, color='red', label='95% CI')
axes[0, 1].axhline(y=long_term_mean, color='green', linestyle=':', linewidth=1.5, label=f'Long-term Mean: ${long_term_mean:.3f}')
axes[0, 1].set_title('Monte Carlo Price Forecast (6 Months)', fontweight='bold')
axes[0, 1].set_xlabel('Days from Today')
axes[0, 1].set_ylabel('Predicted Price (USD)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Distribution of final prices
axes[1, 0].hist(final_prices, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
axes[1, 0].axvline(x=predicted_mean, color='red', linestyle='--', linewidth=2, label=f'Mean: ${predicted_mean:.3f}')
axes[1, 0].axvline(x=confidence_interval_95[0], color='orange', linestyle=':', linewidth=2, label='95% CI')
axes[1, 0].axvline(x=confidence_interval_95[1], color='orange', linestyle=':', linewidth=2)
axes[1, 0].set_title('Distribution of Predicted Prices (6 Months)', fontweight='bold')
axes[1, 0].set_xlabel('Price (USD)')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: ROI Analysis
roi_scenarios = [roi_worst_case, roi_median, roi_mean]
roi_labels = ['Worst Case\n(2.5th %ile)', 'Median', 'Mean']
roi_colors = ['#ff6b6b', '#feca57', '#48dbfb']
bars = axes[1, 1].bar(roi_labels, roi_scenarios, color=roi_colors, edgecolor='black')
axes[1, 1].axhline(y=0, color='black', linewidth=1)
axes[1, 1].set_title('ROI Analysis (2 hectares, $500 loan)', fontweight='bold')
axes[1, 1].set_ylabel('ROI (%)')
axes[1, 1].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, val in zip(bars, roi_scenarios):
    axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                   f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()

# Save the visualization
save_dir = '../outputs/visualizations'
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, 'market_analysis_dashboard.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"✅ Dashboard saved to: {save_path}")

# Show the plot
plt.show()

print("\n" + "="*70)
print("✅ Market Simulation Complete!")
print("="*70)