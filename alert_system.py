import psycopg2
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'api_monitoring',
    'user': 'api_monitor',
    'password': 'monitor123'
}

EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM')
EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD')
EMAIL_TO = os.getenv('ALERT_EMAIL_TO')

CHECK_INTERVAL = int(os.getenv('ALERT_CHECK_INTERVAL', 300))  
COOLDOWN_PERIOD = int(os.getenv('ALERT_COOLDOWN', 600))  

# MODIFIED: Set thresholds to 1 so the email subject indicates urgency immediately
CRITICAL_THRESHOLD = 1  
HIGH_THRESHOLD = 1

last_alert_time = {}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        return None

def get_recent_anomalies(minutes=5):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                detected_at,
                api_name,
                response_time_ms,
                severity,
                details
            FROM anomalies
            WHERE detected_at > NOW() - INTERVAL '{minutes} minutes'
            ORDER BY detected_at DESC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        anomalies = []
        for row in rows:
            anomalies.append({
                'time': row[0],
                'api': row[1],
                'response_time': row[2],
                'severity': row[3],
                'details': row[4]
            })
        
        cursor.close()
        conn.close()
        
        return anomalies
        
    except Exception as e:
        print(f"❌ Error fetching anomalies: {e}")
        if conn:
            conn.close()
        return []

def get_api_health():
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                api_name,
                COUNT(*) as total_requests,
                COUNT(*) FILTER (WHERE success = true) as successful,
                AVG(response_time_ms) as avg_response_time,
                MAX(time) as last_seen
            FROM api_metrics
            WHERE time > NOW() - INTERVAL '10 minutes'
            GROUP BY api_name;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        health = {}
        for row in rows:
            api_name = row[0]
            health[api_name] = {
                'total': row[1],
                'successful': row[2],
                'success_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                'avg_response': round(row[3], 2) if row[3] else 0,
                'last_seen': row[4]
            }
        
        cursor.close()
        conn.close()
        
        return health
        
    except Exception as e:
        print(f"❌ Error fetching health: {e}")
        if conn:
            conn.close()
        return {}

def send_email(subject, body):
    if not EMAIL_FROM or not EMAIL_PASSWORD or not EMAIL_TO:
        print("⚠️  Email not configured! Check .env file")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        # Add HTML body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def create_alert_email(anomalies, api_health):
    # Count by severity
    critical = [a for a in anomalies if a['severity'] == 'critical']
    high = [a for a in anomalies if a['severity'] == 'high']
    medium = [a for a in anomalies if a['severity'] == 'medium']
    
    # Determine overall severity (Using modified low thresholds)
    if len(critical) >= CRITICAL_THRESHOLD:
        overall = "CRITICAL"
        emoji = "🚨"
    elif len(critical) > 0 or len(high) >= HIGH_THRESHOLD:
        overall = "HIGH"
        emoji = "⚠️"
    else:
        overall = "ALERT" # Changed from MEDIUM to ALERT to look more urgent
        emoji = "🔔"
    
    subject = f"{emoji} {overall}: {len(anomalies)} API Anomalies Detected"
    
    # Create HTML body
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background: #d32f2f; color: white; padding: 20px; }}
            .critical {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; }}
            .high {{ background: #fff3e0; border-left: 4px solid #f57c00; padding: 10px; margin: 10px 0; }}
            .medium {{ background: #f1f8e9; border-left: 4px solid #689f38; padding: 10px; margin: 10px 0; }}
            .stats {{ background: #f5f5f5; padding: 15px; margin: 10px 0; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #424242; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{emoji} API Monitoring Alert</h1>
            <p>Severity: {overall} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <h2>📊 Summary</h2>
            <p><strong>Total Anomalies:</strong> {len(anomalies)}</p>
            <p>🔴 Critical: {len(critical)} | 🟡 High: {len(high)} | 🟠 Medium: {len(medium)}</p>
        </div>
    """
    
    # Add anomalies list (showing all, not just critical)
    html += "<h2>🚨 Detected Anomalies</h2>"
    for a in anomalies[:10]:  # Show top 10
        severity_class = "critical" if a['severity'] == 'critical' else "high" if a['severity'] == 'high' else "medium"
        html += f"""
        <div class="{severity_class}">
            <strong>[{a['severity'].upper()}] {a['api']}</strong> at {a['time']}<br>
            Response Time: {a['response_time']:.0f}ms<br>
            {a['details']}
        </div>
        """
    
    # Add API health table
    if api_health:
        html += """
        <h2>💊 API Health Status</h2>
        <table>
            <tr>
                <th>API</th>
                <th>Success Rate</th>
                <th>Avg Response</th>
                <th>Last Seen</th>
            </tr>
        """
        
        for api, stats in api_health.items():
            success_color = "green" if stats['success_rate'] > 95 else "orange" if stats['success_rate'] > 80 else "red"
            html += f"""
            <tr>
                <td>{api}</td>
                <td style="color: {success_color}"><strong>{stats['success_rate']:.1f}%</strong></td>
                <td>{stats['avg_response']:.0f}ms</td>
                <td>{stats['last_seen']}</td>
            </tr>
            """
        
        html += "</table>"
    
    html += """
        <br>
        <p><a href="http://localhost:3000">View Dashboard →</a></p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated alert from your API Monitoring System.<br>
            To stop receiving alerts, update your .env configuration.
        </p>
    </body>
    </html>
    """
    
    return subject, html

# ============================================
# ALERT LOGIC
# ============================================

def should_alert(api_name):
    global last_alert_time
    
    if api_name not in last_alert_time:
        return True
    
    time_since_last = (datetime.now() - last_alert_time[api_name]).total_seconds()
    return time_since_last > COOLDOWN_PERIOD

def check_and_alert():
    print(f"\n{'='*80}")
    print(f"🔍 Checking for anomalies... {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    
    # Get recent anomalies
    check_minutes = CHECK_INTERVAL / 60
    anomalies = get_recent_anomalies(minutes=check_minutes)
    
    if not anomalies:
        print("✅ No anomalies detected - all systems normal")
        return
    
    print(f"⚠️  Found {len(anomalies)} anomalies in last {check_minutes:.0f} minutes")
    
    # Group by API
    by_api = {}
    for a in anomalies:
        api = a['api']
        if api not in by_api:
            by_api[api] = []
        by_api[api].append(a)
    
    # MODIFIED: Check if we should alert (Triggers on ANY anomaly now)
    apis_to_alert = []
    for api, api_anomalies in by_api.items():
        # logic changed: verify if ANY anomalies exist for this API
        # Removed the severity check (e.g. a['severity'] == 'critical')
        # Removed the count threshold check (e.g. count >= CRITICAL_THRESHOLD)
        if len(api_anomalies) > 0 and should_alert(api):
            apis_to_alert.append(api)
    
    if not apis_to_alert:
        print("ℹ️  Anomalies found, but alert is in cooldown")
        return
    
    # Send alert!
    print(f"🚨 Sending alert for: {', '.join(apis_to_alert)}")
    
    # Get API health
    health = get_api_health()
    
    # Create and send email
    subject, body = create_alert_email(anomalies, health)
    
    if send_email(subject, body):
        # Update last alert time
        for api in apis_to_alert:
            last_alert_time[api] = datetime.now()
        print("✅ Alert sent successfully!")
    else:
        print("❌ Failed to send alert")

def run_alert_system():
    print("\n" + "="*80)
    print("🚨 ALERT SYSTEM STARTED (INSTANT TRIGGER MODE)")
    print("="*80)
    print(f"📧 Alerts will be sent to: {EMAIL_TO}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60:.0f} minutes)")
    print(f"🔕 Cooldown period: {COOLDOWN_PERIOD} seconds ({COOLDOWN_PERIOD/60:.0f} minutes)")
    print("="*80)
    print("\n⚠️  Press Ctrl+C to stop\n")
    
    # Validate email configuration
    if not EMAIL_FROM or not EMAIL_PASSWORD or not EMAIL_TO:
        print("❌ Email not configured!")
        print("💡 Please set ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD, ALERT_EMAIL_TO in .env file")
        return
    
    try:
        while True:
            check_and_alert()
            
            print(f"\n💤 Sleeping for {CHECK_INTERVAL} seconds...")
            print(f"⏰ Next check at: {(datetime.now() + timedelta(seconds=CHECK_INTERVAL)).strftime('%H:%M:%S')}\n")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("🛑 ALERT SYSTEM STOPPED")
        print("="*80)
        print("\n👋 Goodbye!\n")

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    run_alert_system()