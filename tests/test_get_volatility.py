import sys
import traceback

sys.path.insert(0, ".")

print("Starting test...", flush=True)

try:
    print("Importing...", flush=True)
    from app import get_volatility

    # Test get_volatility directly
    print("Testing get_volatility()...", flush=True)
    result = get_volatility()
    print(f"Result type: {type(result)}", flush=True)
    print(f"Result: {result}", flush=True)
    print("\nSuccess!", flush=True)

except Exception as e:
    print(f"Error: {e}", flush=True)
    traceback.print_exc()
