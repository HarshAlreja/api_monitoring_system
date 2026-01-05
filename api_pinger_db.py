import requests
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch

# ============================================
# DATABASE CONNECTION
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'api_monitoring',
    'user': 'api_monitor',
    'password': 'monitor123'
}

# ============================================
# API CONFIGURATION
# ============================================

APIS=[
    {
        'name':'JSONPlaceholder',
        'url':'https://jsonplaceholder.typicode.com/',

    },
    {
        'name':'PokeAPI',
        'url':'https://pokeapi.co/'

    },
    {
        'name':'CatFacts',
        'url':'https://catfact.ninja/'
    },
    
    {
        'name': 'IPify',
        'url': 'https://www.ipify.org/'
    },
    {
        'name': 'RandomUser',
        'url': 'https://randomuser.me/'
    },
    
    {
        'name': 'GitHub',
        'url': 'https://api.github.com'
    }
    
]

PING_INTERVAL = 15  # seconds
TIMEOUT = 30  # seconds

# ============================================
# DATABASE FUNCTIONS
# ============================================

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def save_to_database(results):
    """Save results to TimescaleDB"""
    if not results:
        return
    
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database!")
        return
    
    try:
        cursor = conn.cursor()
        
        # Prepare data for insertion
        insert_query = """
            INSERT INTO api_metrics 
            (time, api_name, response_time_ms, status_code, success, response_size_bytes, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        data_to_insert = [
            (
                result['timestamp'],
                result['api_name'],
                result['response_time_ms'],
                result['status_code'],
                result['success'],
                result['response_size_bytes'],
                result['error_message']
            )
            for result in results
        ]
        
        # Batch insert for efficiency
        execute_batch(cursor, insert_query, data_to_insert)
        conn.commit()
        
        print(f"💾 Saved {len(results)} results to database")
        
        # Show total rows in database
        cursor.execute("SELECT COUNT(*) FROM api_metrics")
        total_rows = cursor.fetchone()[0]
        print(f"📊 Total rows in database: {total_rows}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        if conn:
            conn.rollback()
            conn.close()

# ============================================
# PING FUNCTIONS
# ============================================

def ping_single_api(api_name, api_url):
    """Ping a single API and return metrics"""
    start_time = time.time()
    
    try:
        response = requests.get(api_url, timeout=TIMEOUT)
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000, 2)
        response_size = len(response.content)
        is_success = 200 <= response.status_code < 300
        
        result = {
            'timestamp': datetime.now(),
            'api_name': api_name,
            'response_time_ms': response_time_ms,
            'status_code': response.status_code,
            'success': is_success,
            'response_size_bytes': response_size,
            'error_message': None if is_success else f'HTTP {response.status_code}'
        }
        
        status = "✅" if is_success else "⚠️"
        print(f"{status} {api_name:20s} | {response_time_ms:7.0f}ms | Status: {response.status_code}")
        
        return result
        
    except requests.Timeout:
        result = {
            'timestamp': datetime.now(),
            'api_name': api_name,
            'response_time_ms': None,
            'status_code': None,
            'success': False,
            'response_size_bytes': None,
            'error_message': f'Timeout after {TIMEOUT}s'
        }
        print(f"⏱️  {api_name:20s} | TIMEOUT")
        return result
        
    except Exception as e:
        result = {
            'timestamp': datetime.now(),
            'api_name': api_name,
            'response_time_ms': None,
            'status_code': None,
            'success': False,
            'response_size_bytes': None,
            'error_message': f'Error: {str(e)}'
        }
        print(f"💥 {api_name:20s} | ERROR: {str(e)}")
        return result

def ping_all_apis():
    """Ping all configured APIs"""
    print(f"\n{'='*80}")
    print(f"🔄 Pinging {len(APIS)} APIs at {datetime.now().strftime('%H:%M:%S')}...")
    print(f"{'='*80}")
    
    results = []
    for api in APIS:
        result = ping_single_api(api['name'], api['url'])
        results.append(result)
    
    print(f"{'='*80}")
    print(f"✅ Completed {len(results)} pings")
    return results

# ============================================
# MAIN MONITORING LOOP
# ============================================

def monitor_forever():
    """Main monitoring loop"""
    print(f"\n{'='*80}")
    print("🚀 API MONITORING SYSTEM - DATABASE MODE")
    print(f"{'='*80}")
    print(f"📊 Monitoring {len(APIS)} APIs")
    print(f"⏱️  Ping interval: {PING_INTERVAL} seconds")
    print(f"⏳ Timeout: {TIMEOUT} seconds")
    print(f"💾 Database: TimescaleDB on localhost:5432")
    print(f"{'='*80}")
    print("\n⚠️  Press Ctrl+C to stop\n")
    
    # Test database connection
    print("🔌 Testing database connection...")
    conn = get_db_connection()
    if conn:
        print("✅ Database connected successfully!")
        conn.close()
    else:
        print("❌ Database connection failed! Check if Docker containers are running.")
        print("   Run: docker ps")
        return
    
    ping_count = 0
    
    try:
        while True:
            ping_count += 1
            print(f"\n🔄 PING ROUND #{ping_count}")
            results = ping_all_apis()
            save_to_database(results)
            print(f"\n💤 Sleeping {PING_INTERVAL}s...\n")
            time.sleep(PING_INTERVAL)
    
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print("🛑 MONITORING STOPPED")
        print(f"{'='*80}")
        print(f"📊 Total rounds: {ping_count}")
        print(f"💾 All data saved to database")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    monitor_forever()