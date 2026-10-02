import os
import sys
from db_client import get_supabase_client

def test_connection():
    print("Testing Supabase connection for project: tllwqxxnybzxcpkdpnaz...")
    try:
        client = get_supabase_client()
        # Query public tables to test connection and permissions
        res = client.table("patient_intakes").select("count", count="exact").limit(0).execute()
        print(f"SUCCESS: Connected to Supabase! Found {res.count} existing patient records in 'patient_intakes'.")
    except Exception as e:
        print("\nCONNECTION FAILED or TABLES NOT CREATED YET.")
        print(f"Error details: {e}")
        print("\nPlease make sure:")
        print("1. You added your SUPABASE_SERVICE_KEY in D:\\NUML_FYP\\models\\.env")
        print("2. You ran the SQL migration script in your Supabase SQL editor: https://supabase.com/dashboard/project/tllwqxxnybzxcpkdpnaz/sql/new")

if __name__ == "__main__":
    test_connection()
