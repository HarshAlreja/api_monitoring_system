import requests
import time
import csv
from datetime import datetime
import os 

APIS=[
    {
        'name':'Wikipedia',
        'url':'https://www.wikipedia.org/',
        'description':'Mega traffic , ultra-fast CDN'
    },
    {
        'name':'GitHub',
        'url':'https://github.com/',
        'description':'high traffic considered'
    },
    {
        'name':'Redit',
        'url':'https://www.reddit.com/',
        'description':'Variable performance'
    },
        {
        'name': 'JSONPlaceholder',
        'url': 'https://jsonplaceholder.typicode.com/posts/1',
        'description': 'Test API, consistent baseline'
    },
    {
        'name': 'PokeAPI',
        'url': 'https://pokeapi.co/api/v2/pokemon/pikachu',
        'description': 'Community API, slower'
    },
    {
        'name': 'Cloudflare',
        'url': 'https://one.one.one.one/',
        'description': 'Edge-cached, extremely fast'
    },
    {
        'name': 'HackerNews',
        'url': 'https://hacker-news.firebaseio.com/',
        'description': 'Firebase-backed, fast'
    },
    {
        'name': 'RESTCountries',
        'url': 'https://restcountries.com/',
        'description': 'International API, moderate speed'
    }
]
PING_INTERVAL=15
TIMEOUT=30
CSV_FILENAME='api_monitoring_data.csv'

CSV_HEADERS=[
    'timestamp','api_name','response_time_ms','status_code','success','response_size_bytes',
    'error_message'
]

def ping_single_api(api_name,api_url):
    start_time = time.time()
    try:
        response=requests.get(api_url,timeout=TIMEOUT)
        end_time=time.time()
        response_time_ms=round((end_time-start_time)*1000,2)
        response_size=len(response.content)
        is_success=response.status_code>=200 and response.status_code<300

        result={
            'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'api_name':api_name,
            # REMOVED 'url' - not in headers
            'response_time_ms':response_time_ms,
            'status_code':response.status_code,
            'success':is_success,
            'response_size_bytes':response_size,  # FIXED: added 's'
            'error_message':None if is_success else f'HTTP {response.status_code}'
        }

        status="✅" if is_success else "❌"
        print(f"{status} {api_name:20s}| {response_time_ms:7.0f}ms | Status: {response.status_code}")
        return result
    
    except requests.Timeout:
        end_time=time.time()
        response_time_ms=round((end_time-start_time)*1000,2)
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'api_name': api_name,
            'response_time_ms': None,  
            'status_code': None,
            'success': False,
            'response_size_bytes': None,
            'error_message': f'Timeout after {TIMEOUT}s'
        }

        print(f"⏱️  {api_name:20s} | TIMEOUT after {TIMEOUT}s")
        return result
    
    except requests.ConnectionError:
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'api_name': api_name,
            'response_time_ms': None,
            'status_code': None,
            'success': False,
            'response_size_bytes': None,
            'error_message': 'Connection failed - API might be down'
        }
        
        print(f"❌ {api_name:20s} | CONNECTION ERROR")
        return result
        
    except Exception as e:
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'api_name': api_name,
            'response_time_ms': None,
            'status_code': None,
            'success': False,
            'response_size_bytes': None,
            'error_message': f'Unexpected error: {str(e)}'
        }
        print(f"💥 {api_name:20s}| ERROR :{str(e)}")
        return result

def ping_all_apis():
    print(f"\n{'='*50}")
    print(f"Pinging{len(APIS)} APIS at {datetime.now().strftime('%H:%M:%S')}...")
    print(f"\n{'='*50}")
    results=[]

    for api in APIS:
        result=ping_single_api(api['name'],api['url'])
        results.append(result)
    print(f"\n{'='*50}")
    print(f"Completed{len(results)} ping")
    return results




def save_to_csv(results):
    file_exists=os.path.isfile(CSV_FILENAME)
    try:
        with open(CSV_FILENAME,'a',newline='',encoding='utf-8') as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=CSV_HEADERS)

            if not file_exists:
                writer.writeheader()
                print(f"Created new csv File:{CSV_FILENAME}")
            writer.writerows(results)
            print(f"Saved {len(results)} results to {CSV_FILENAME}")
    except Exception as e:
        print(f"Error Saving to CSV: {e}")



def monitor_forever():
    print(f"\n{'='*50}")
    print("API monitoring system started")
    print(f"\n{'='*50}")
    print(f"monitoring{len(APIS)} APIs") 
    print(f"Ping interval: {PING_INTERVAL} seconds")
    print(f"Timeout:{TIMEOUT} seconds")
    print(f"Data File:{CSV_FILENAME}")
    print(f"\n{'='*50}")
    ping_count=0

    try:
        while True:
            ping_count+=1
            print(f"Ping round {ping_count}")
            results=ping_all_apis()
            save_to_csv(results)
            print(f"\nSleeping for {PING_INTERVAL}seconds...\n")
            time.sleep(PING_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n{'='*50}")   
        print(f"Monitoring stopped by user")
        print(f"\n{'='*50}")
        print(f"\nTotal ping rounds completed: {ping_count}")
        print(f"All data saved to {CSV_FILENAME}")
        print(f"\n{'='*50}")


if __name__=="__main__":
    monitor_forever()    







