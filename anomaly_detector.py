"""
Anomaly Detection System
Detects unusual API behavior using Isolation Forest ML model
Analyzes last 7 days of data by default
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ============================================
# DATABASE CONFIGURATION
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'api_monitoring',
    'user': 'api_monitor',
    'password': 'monitor123'
}

# Default: Analyze last 7 days
DEFAULT_HOURS = 168  # 7 days = 168 hours

# ============================================
# DATABASE SETUP FUNCTIONS
# ============================================

def get_db_connection():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_anomaly_table():
    """Create table for storing detected anomalies"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Drop existing table to avoid duplicates
        cursor.execute("DROP TABLE IF EXISTS anomalies;")
        
        # Create anomalies table
        cursor.execute("""
            CREATE TABLE anomalies (
                id SERIAL PRIMARY KEY,
                detected_at TIMESTAMPTZ NOT NULL,
                api_name TEXT NOT NULL,
                response_time_ms FLOAT,
                anomaly_score FLOAT,
                is_anomaly BOOLEAN,
                severity TEXT,
                details TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX idx_anomalies_time 
            ON anomalies (detected_at DESC);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_anomalies_api 
            ON anomalies (api_name, detected_at DESC);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_anomalies_severity
            ON anomalies (severity, detected_at DESC);
        """)
        
        conn.commit()
        print("✅ Anomaly table created (fresh)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        if conn:
            conn.close()
        return False

# ============================================
# DATA FETCHING
# ============================================

def fetch_training_data(hours=DEFAULT_HOURS):
    """
    Fetch recent data for training ML model
    
    Args:
        hours: How many hours of historical data to use (default: 168 = 7 days)
    
    Returns:
        DataFrame with API metrics
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Get data from last N hours
        query = f"""
            SELECT 
                time,
                api_name,
                response_time_ms,
                status_code,
                success
            FROM api_metrics
            WHERE time > NOW() - INTERVAL '{hours} hours'
                AND response_time_ms IS NOT NULL
            ORDER BY time DESC;
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        days = hours / 24
        print(f"📊 Fetched {len(df)} records from last {days:.1f} days")
        
        if not df.empty:
            time_range = df['time'].max() - df['time'].min()
            print(f"📅 Time range: {time_range}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        if conn:
            conn.close()
        return None

# ============================================
# FEATURE ENGINEERING
# ============================================

def create_features(df):
    """
    Create ML features from raw data
    
    Features:
    - Response time
    - Rolling average (last 10 requests)
    - Standard deviation
    - Rate of change
    - Hour of day (to detect time-based patterns)
    """
    if df.empty:
        return df
    
    # Sort by API and time
    df = df.sort_values(['api_name', 'time'])
    
    # Extract time features
    df['hour'] = pd.to_datetime(df['time']).dt.hour
    df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
    
    # Group by API to calculate rolling stats
    features_list = []
    
    for api_name, group in df.groupby('api_name'):
        group = group.copy()
        
        # Rolling statistics (last 10 requests)
        group['rolling_mean'] = group['response_time_ms'].rolling(window=10, min_periods=1).mean()
        group['rolling_std'] = group['response_time_ms'].rolling(window=10, min_periods=1).std().fillna(0)
        group['rolling_min'] = group['response_time_ms'].rolling(window=10, min_periods=1).min()
        group['rolling_max'] = group['response_time_ms'].rolling(window=10, min_periods=1).max()
        
        # Deviation from rolling mean
        group['deviation'] = abs(group['response_time_ms'] - group['rolling_mean'])
        
        # Percentage deviation
        group['pct_deviation'] = np.where(
            group['rolling_mean'] > 0,
            (group['deviation'] / group['rolling_mean']) * 100,
            0
        )
        
        # Rate of change
        group['rate_of_change'] = group['response_time_ms'].diff().fillna(0)
        
        # Z-score (how many standard deviations from mean)
        group['z_score'] = np.where(
            group['rolling_std'] > 0,
            (group['response_time_ms'] - group['rolling_mean']) / group['rolling_std'],
            0
        )
        
        features_list.append(group)
    
    result = pd.concat(features_list, ignore_index=True)
    print(f"✅ Created features for {len(result)} data points")
    
    # Show feature statistics
    print(f"   - APIs: {result['api_name'].nunique()}")
    print(f"   - Time span: {result['time'].min()} to {result['time'].max()}")
    
    return result

# ============================================
# ANOMALY DETECTION MODEL
# ============================================

def train_and_detect_anomalies(df, contamination=0.05):
    """
    Train Isolation Forest model and detect anomalies
    
    Args:
        df: DataFrame with features
        contamination: Expected percentage of anomalies (default 5%)
    
    Returns:
        DataFrame with anomaly predictions
    """
    if df.empty or len(df) < 50:
        print(f"⚠️  Not enough data for training (have {len(df)}, need at least 50)")
        return df
    
    print(f"\n🧠 Training Isolation Forest model...")
    print(f"   - Contamination rate: {contamination*100}%")
    
    # Select features for ML model
    feature_columns = [
        'response_time_ms',
        'rolling_mean',
        'rolling_std',
        'deviation',
        'pct_deviation',
        'rate_of_change',
        'z_score',
        'hour',
        'day_of_week'
    ]
    
    # Prepare data
    X = df[feature_columns].values
    
    # Handle any remaining NaN values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Standardize features (important for ML!)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Isolation Forest
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples='auto',
        n_jobs=-1  # Use all CPU cores
    )
    
    print("🔄 Training model...")
    model.fit(X_scaled)
    
    # Predict anomalies
    # -1 = anomaly, 1 = normal
    predictions = model.predict(X_scaled)
    
    # Get anomaly scores (lower = more anomalous)
    scores = model.decision_function(X_scaled)
    
    # Normalize scores to 0-1 range for easier interpretation
    scores_normalized = (scores - scores.min()) / (scores.max() - scores.min())
    
    # Add predictions to dataframe
    df['is_anomaly'] = predictions == -1
    df['anomaly_score'] = scores
    df['anomaly_score_normalized'] = scores_normalized
    
    # Classify severity based on normalized score
    def get_severity(score_norm, is_anomaly):
        if not is_anomaly:
            return 'normal'
        elif score_norm < 0.2:
            return 'critical'
        elif score_norm < 0.4:
            return 'high'
        else:
            return 'medium'
    
    df['severity'] = df.apply(
        lambda row: get_severity(row['anomaly_score_normalized'], row['is_anomaly']),
        axis=1
    )
    
    anomaly_count = df['is_anomaly'].sum()
    normal_count = len(df) - anomaly_count
    
    print(f"✅ Model trained!")
    print(f"   - Normal: {normal_count} ({normal_count/len(df)*100:.1f}%)")
    print(f"   - Anomalies: {anomaly_count} ({anomaly_count/len(df)*100:.1f}%)")
    
    return df

# ============================================
# SAVE ANOMALIES TO DATABASE
# ============================================

def save_anomalies(df):
    """Save detected anomalies to database"""
    # Filter only anomalies
    anomalies = df[df['is_anomaly'] == True].copy()
    
    if anomalies.empty:
        print("✅ No anomalies detected - all systems normal!")
        return True
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Prepare data for insertion
        saved_count = 0
        for _, row in anomalies.iterrows():
            details = f"Response: {row['response_time_ms']:.0f}ms, " \
                     f"Expected: {row['rolling_mean']:.0f}ms, " \
                     f"Deviation: {row['deviation']:.0f}ms ({row['pct_deviation']:.1f}%), " \
                     f"Z-score: {row['z_score']:.2f}"
            
            cursor.execute("""
                INSERT INTO anomalies 
                (detected_at, api_name, response_time_ms, anomaly_score, 
                 is_anomaly, severity, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['time'],
                row['api_name'],
                float(row['response_time_ms']),
                float(row['anomaly_score']),
                True,
                row['severity'],
                details
            ))
            saved_count += 1
        
        conn.commit()
        print(f"💾 Saved {saved_count} anomalies to database")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error saving anomalies: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

# ============================================
# REPORTING
# ============================================

def print_detailed_report(df):
    """Print detailed analysis report"""
    
    print("\n" + "="*80)
    print("📋 DETAILED ANOMALY REPORT")
    print("="*80)
    
    total_points = len(df)
    total_anomalies = df['is_anomaly'].sum()
    anomaly_percentage = (total_anomalies / total_points) * 100 if total_points > 0 else 0
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total data points analyzed: {total_points}")
    print(f"   Anomalies detected: {total_anomalies} ({anomaly_percentage:.1f}%)")
    print(f"   Normal behavior: {total_points - total_anomalies} ({100-anomaly_percentage:.1f}%)")
    
    if total_anomalies > 0:
        print(f"\n🔍 ANOMALIES BY API:")
        anomaly_by_api = df[df['is_anomaly'] == True].groupby('api_name').agg({
            'is_anomaly': 'count',
            'response_time_ms': ['mean', 'min', 'max']
        }).round(2)
        
        for api in anomaly_by_api.index:
            count = int(anomaly_by_api.loc[api, ('is_anomaly', 'count')])
            avg = anomaly_by_api.loc[api, ('response_time_ms', 'mean')]
            min_time = anomaly_by_api.loc[api, ('response_time_ms', 'min')]
            max_time = anomaly_by_api.loc[api, ('response_time_ms', 'max')]
            print(f"   - {api}: {count} anomalies")
            print(f"     Response times: {min_time:.0f}ms - {max_time:.0f}ms (avg: {avg:.0f}ms)")
        
        print(f"\n⚠️  SEVERITY BREAKDOWN:")
        severity_counts = df[df['is_anomaly'] == True]['severity'].value_counts()
        for severity, count in severity_counts.items():
            emoji = "🔴" if severity == "critical" else "🟡" if severity == "high" else "🟠"
            print(f"   {emoji} {severity.upper()}: {count}")
        
        # Top 5 worst anomalies
        print(f"\n🚨 TOP 5 WORST ANOMALIES:")
        worst = df[df['is_anomaly'] == True].nsmallest(5, 'anomaly_score_normalized')
        for idx, row in worst.iterrows():
            print(f"   - {row['api_name']} at {row['time']}")
            print(f"     {row['response_time_ms']:.0f}ms (expected {row['rolling_mean']:.0f}ms)")
            print(f"     Severity: {row['severity'].upper()}")
    
    print("\n" + "="*80)

# ============================================
# MAIN ANALYSIS FUNCTION
# ============================================

def run_anomaly_detection(hours=DEFAULT_HOURS, contamination=0.05):
    """
    Main function to run complete anomaly detection pipeline
    
    Args:
        hours: Hours of historical data to analyze (default: 168 = 7 days)
        contamination: Expected anomaly rate (default: 0.05 = 5%)
    """
    
    print("\n" + "="*80)
    print("🤖 ANOMALY DETECTION SYSTEM")
    print("="*80)
    print(f"📅 Analyzing last {hours/24:.1f} days of data")
    print(f"🎯 Expected anomaly rate: {contamination*100}%")
    print("="*80)
    
    # Step 1: Setup database
    print("\n📊 Step 1: Setting up database...")
    if not create_anomaly_table():
        print("❌ Failed to setup database")
        return False
    
    # Step 2: Fetch training data
    print(f"\n📊 Step 2: Fetching last {hours} hours of data...")
    df = fetch_training_data(hours=hours)
    
    if df is None or df.empty:
        print("❌ No data available for analysis")
        print("💡 Make sure api_pinger_db.py is running and collecting data!")
        return False
    
    print(f"✅ Got {len(df)} data points from {df['api_name'].nunique()} APIs")
    
    # Step 3: Feature engineering
    print("\n📊 Step 3: Creating ML features...")
    df = create_features(df)
    
    # Step 4: Train model and detect anomalies
    print("\n📊 Step 4: Detecting anomalies with ML...")
    df = train_and_detect_anomalies(df, contamination=contamination)
    
    # Step 5: Save results
    print("\n📊 Step 5: Saving anomalies to database...")
    save_anomalies(df)
    
    # Step 6: Detailed report
    print_detailed_report(df)
    
    print("\n✅ Anomaly detection complete!")
    print("="*80 + "\n")
    
    return True

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    import sys
    
    # Allow command-line arguments
    hours = DEFAULT_HOURS
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
            print(f"📅 Using custom time range: {hours} hours ({hours/24:.1f} days)")
        except:
            print(f"⚠️  Invalid hours argument, using default: {DEFAULT_HOURS} hours")
    
    # Run anomaly detection
    success = run_anomaly_detection(hours=hours)
    
    if success:
        print("🎉 Successfully completed anomaly detection!")
        print("💡 Now visualize anomalies in Grafana!")
    else:
        print("❌ Anomaly detection failed")
        print("💡 Check if Docker is running and pinger has collected data")