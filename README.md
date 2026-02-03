🎯 API Monitoring Anomaly Detection System
Production-grade system for real-time API monitoring with ML-powered anomaly detection using Isolation Forest, instant email alerts, TimescaleDB storage, and Grafana visualization—all Dockerized.🚀 
Key FeaturesMonitors 8+ APIs every 15 seconds (JSONPlaceholder, PokeAPI, CatFacts, BoredAPI, IPify, RandomUser, JokesAPI, GitHub).Unsupervised Anomaly Detection: Isolation Forest isolates outliers via shorter random tree paths (scores -1 to 1; <0 indicates anomaly, lower=more anomalous). 
scikit-learnAutomated Periodic Status Reports: Sends a comprehensive email digest every 5 minutes detailing which websites are performing slowly. This ensures proactive monitoring even when you aren't actively checking the dashboard.
Rich Features: rolling mean/std (window=10), Z-score $z = \frac{x - \mu}{\sigma}$, % deviation, rate of change, hour/day patterns from 7-day data. scikit-learnSeverity Tiers: Critical (score <-0.2), High (<-0.4), Medium. stackoverflowConfigurable SMTP Alerts: Gmail integration for both instant anomaly alerts and periodic status summaries with configurable intervals and cooldowns.Grafana Dashboards: time-series metrics, anomaly heatmaps. github🏗️ 

Architecture

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ API Pinger          │────▶│ TimescaleDB         │────▶│ Anomaly Detector    │
│ (apipingerdb.py)    │     │ Hypertables:        │     │ (anomalydetector.py)│
│ - 15s polls         │     │   api_metrics       │     │ - Trains Isolation  │
│ - Inserts metrics   │     │   anomalies         │     │   Forest (n_estimators│
└──────────────┬──────┘     └────────────┬────────┘     │   =100, contam=0.1)  │
               │                           │              │ - Labels & scores   │
               │                           │              └────────────┬────────┘
               ▼                           ▼                           │
┌─────────────────────┐     ┌─────────────────────┐                  ▼
│ Alert System        │◄────│ Grafana Queries     │◄───────────────── │
│ (alertsystem.py)    │     │ - time_bucket('15s')│                  │
│ - Polls DB          │     │ - avg(response_time)│                  │
│ - SMTP on critical  │     │ by api, time        │                  │
│ - 5-min Status Rpts │     └─────────────────────┘                  │
└─────────────────────┘                                              │
                                                                    │
                                                              ┌──────────────┐
                                                              │ Docker Compose│
                                                              │ - healthchecks│
                                                              │ - depends_on  │
                                                              └──────────────┘
Pinger → DB → (Detector trains/labels | Alerts poll/send | Grafana queries).

🛠️ Tech StackCategoryTools/LibrariesRoleLanguagePython 3.8+Core logicHTTP/DBrequests, psycopg2Calls, Timescale connML/Datascikit-learn (IsolationForest), pandas, numpyAnomaly detection, featuresAlerts/Configsmtplib, python-dotenvEmails, .envInfraDocker Compose, TimescaleDB, GrafanaDeployment, storage, vizAnomaly Detection Deep DiveIsolation Forest builds n_estimators (e.g., 100) random trees; anomalies isolated quicker (avg path < normal).

 Anomaly score $s(x^{(i)}, n) = 2^{-\frac{E(h(x^{(i)}))}{c(n)}}$, where $h$ is path length, $c(n)$ 
 normalization; s<0.5=outlier. mbrenndoerferFeatures 
 
 
 
Table:| Feature          | Formula/Description                            | Purpose|------------------|----------------------------------------------|------------------| Rolling Mean     | $\mu_{10}$ past 10 reqs                  | Local trend| Rolling Std      | $\sigma_{10}$                            | Volatility| Z-Score          | $z = \frac{rt - \mu_{60}}{\sigma_{60}}$  | Deviation| % Deviation      | $\frac{rt - \mu}{|\mu|} \times 100$      | Relative change| Rate of Change   | $\frac{rt_t - rt_{t-1}}{rt_{t-1}}$       | Acceleration| Time Features    | hour(0-23), weekday(0-6)                     | 

PatternsModel retrains periodically on unlabeled data (contamination~0.1). scikit-learn📊 Grafana Setup ExamplesConnect to TimescaleDB datasource. Sample queries: slingacademySQL# Response time trend

SELECT time_bucket('15m', timestamp) AS time,
       api_name,
       AVG(response_time_ms) AS avg_rt,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95
FROM api_metrics
GROUP BY 1, 2 ORDER BY 1;

# Anomalies heatmap
SELECT time_bucket('1h', timestamp) AS time,
       api_name,
       AVG(anomaly_score) AS avg_score,
       COUNT(*) FILTER (WHERE anomaly_score < -0.2) AS critical_count
FROM anomalies WHERE anomaly_score < 0
GROUP BY 1, 2;

Panels: Time series, stat (alerts fired), heatmap (scores).🚀 Quick Startgit clone https://github.com/HarshAlreja/api_monitoring_system.git && cd api_monitoring_system.env (Gmail app pass required)Code snippetDB_HOST=localhost DB_NAME=apimonitoring DB_USER=apimonitor DB_PASS=monitor123
ALERT_EMAIL_FROM=your@gmail.com ALERT_EMAIL_PASSWORD=apppass ALERT_EMAIL_TO=to@gmail.com

ALERT_CHECK_INTERVAL=300 # 5 minutes for status reports
ALERT_COOLDOWN=600

docker-compose up -d (adds healthchecks: healthcheck: test: ["CMD", "pg_isready"]). oneuptimepip install -r requirements.txtTerminals:python api_pinger_db.pypython alert_system.pypython anomaly_detector.pyGrafana: localhost:3000 (username/password).

🔧 Configuration & CustomizationAdd APIs: Edit api_pinger_db.py endpoints list.Tune ML: contamination=0.05-0.2, max_samples='auto' in IsolationForest. scikit-learnDocker health: Add to compose.yaml for depends_on condition: service_healthy. oneuptime

📈 Performance & EffectivenessAccuracy: Isolation Forest ~90%+ on benchmarks vs. thresholds; adapts to drifts. geeksforgeeksLatency: <1s detection post-ping; scales with CPU cores (parallel trees). 

scikit-learnReliability: Docker healthchecks ensure DB ready; cooldowns prevent alert storms. last9🛤️ RoadmapPhaseStatusItems1: Core✅Pinger, DB, Docker2: ML/Alerts✅Forest, features, SMTP, 5-min Status Reports4: Advanced📋Slack/MS Teams alerts, auto-scaling, Prometheus exportProgress: 80% (Feb 2026 log).

🤝 ContributingFork & branch: git checkout -b feat/enhance-dashCommit: Conventional (feat:, fix:); lint with black. readmecodegenPR: Describe changes, add tests.

📄 LicenseMIT LicenseCopyright (c) 2026 Harsh Alreja👤 Harsh Alreja | alrejaharsh38@gmail.com | GitHub