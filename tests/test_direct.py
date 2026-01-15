import sys
import traceback

sys.path.insert(0, ".")

try:
    from src.app import app, advanced_calc

    # Test calculate_volatility_metrics directly
    print("Testing calculate_volatility_metrics()...")
    result = advanced_calc.calculate_volatility_metrics()
    print("Result:", result)
    print("\nSuccess!")

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
