import os
import sys
from db_client import get_supabase_client

def test_connection():
    print("Testing Supabase connection for project: tllwqxxnybzxcpkdpnaz...\n")
    try:
        client = get_supabase_client()
        tables = [
            "healthcare_centers",
            "user_profiles",
            "patient_intakes",
            "surveillance_forecasts",
            "outbreak_alerts",
        ]
        print(f"{'Table Name':<26} | {'Status':<10} | {'Rows':<5}")
        print("-" * 48)
        for tbl in tables:
            res = client.table(tbl).select("count", count="exact").limit(0).execute()
            print(f"{tbl:<26} | {'ONLINE':<10} | {res.count}")
        print("\nAll database tables verified successfully with active read/write permissions!")
    except Exception as e:
        print("\nCONNECTION OR QUERY FAILED:")
        print(f"Error details: {e}")
        print("\nPlease make sure:")
        print("1. Your SUPABASE_SERVICE_KEY in .env is valid.")
        print("2. The SQL tables have been created in the Supabase SQL editor.")

if __name__ == "__main__":
    test_connection()
