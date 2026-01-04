# 🎯 API Monitoring & Anomaly Detection System

> A production-grade API monitoring system with real-time anomaly detection, predictive analytics, and beautiful Grafana dashboards.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 📋 Project Overview

An intelligent API monitoring system that:
- 🔄 Monitors multiple APIs in real-time (15-second intervals)
- 🤖 Detects anomalies using machine learning
- 📊 Visualizes metrics with Grafana dashboards
- 🔮 Predicts API failures before they happen
- 🐳 Runs entirely in Docker containers
- 📈 Stores time-series data in TimescaleDB

**Why this project?**  
Every production system depends on external APIs (payments, authentication, data). This system detects problems *before* they impact users, enabling proactive responses and better user experience.

---

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.8+** - Data collection and ML models
- **TimescaleDB** - Time-series database (PostgreSQL-based)
- **Grafana** - Real-time visualization dashboards
- **Docker & Docker Compose** - Containerization

### Python Libraries
- `requests` - API calls
- `psycopg2` - Database connectivity
- `scikit-learn` - Anomaly detection
- `prophet` / `statsmodels` - Time-series forecasting
- `pandas` - Data analysis

### Infrastructure (Coming Soon)
- GitHub Actions - CI/CD pipeline
- Prometheus - Metrics collection
- Redis - Caching layer

---

## 🏗️ Architecture
```
┌─────────────────┐
│  Python Pinger  │ ──→ Pings APIs every 15s
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  TimescaleDB    │ ──→ Stores time-series data
└────────┬────────┘
         │
         ├──→ ML Models (Anomaly Detection)
         │
         └──→ Grafana (Visualization)
```

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- Python 3.8+
- 8GB RAM recommended

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/api-monitoring-system.git
cd api-monitoring-system
```

### 2. Start Docker Containers
```bash
docker-compose up -d
```

This starts:
- **TimescaleDB** on `localhost:5432`
- **Grafana** on `localhost:3000`

### 3. Set Up Database
```bash
docker exec -it api_monitor_db psql -U api_monitor -d api_monitoring

# Inside psql, run:
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE api_metrics (
    time TIMESTAMPTZ NOT NULL,
    api_name TEXT NOT NULL,
    response_time_ms DOUBLE PRECISION,
    status_code INTEGER,
    success BOOLEAN,
    response_size_bytes INTEGER,
    error_message TEXT
);

SELECT create_hypertable('api_metrics', 'time');
CREATE INDEX idx_api_name ON api_metrics (api_name, time DESC);

\q
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Start Monitoring
```bash
python api_pinger_db.py
```

### 6. Access Grafana
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `admin123`

---

## 📊 What's Being Monitored

Currently tracking 8 public APIs:
- JSONPlaceholder (Test API)
- PokeAPI (Pokemon data)
- CatFacts (Random facts)
- BoredAPI (Activity suggestions)
- IPify (IP address lookup)
- RandomUser (User data generator)
- JokesAPI (Random jokes)
- GitHub API (Developer platform)

**Metrics collected:**
- Response time (milliseconds)
- Status code (200, 404, 500, etc.)
- Success rate
- Response size
- Error messages

---

## 🎯 Project Roadmap

### ✅ Phase 1: Foundation (COMPLETED)
- [x] Basic API pinger with CSV storage
- [x] Docker setup (TimescaleDB + Grafana)
- [x] Database schema design
- [x] Real-time data collection

### 🔄 Phase 2: Visualization (IN PROGRESS)
- [ ] Grafana dashboard design
- [ ] Response time graphs
- [ ] Success rate monitoring
- [ ] API comparison views

### ⏳ Phase 3: Machine Learning (UPCOMING)
- [ ] Anomaly detection (Isolation Forest)
- [ ] Time-series forecasting (Prophet/ARIMA)
- [ ] Failure prediction model
- [ ] Pattern recognition

### ⏳ Phase 4: Production Features (UPCOMING)
- [ ] Authentication support (API keys, OAuth)
- [ ] Alert system (Email, Slack)
- [ ] Rate limiting handling
- [ ] Advanced error handling

### ⏳ Phase 5: MLOps & Deployment (UPCOMING)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing
- [ ] Model retraining automation
- [ ] Prometheus monitoring
- [ ] Documentation

---

## 📈 Current Progress
```
[████████░░░░░░░░░░░░] 40% Complete

✅ Data collection working
✅ Docker infrastructure set up
✅ Database schema created
🔄 Building dashboards
⏳ ML models next
⏳ Production deployment coming
```

---

## 🧪 Running Tests
```bash
# Coming soon!
pytest tests/
```

---

## 📝 Development Log

### Day 1 (Jan 4, 2026)
- ✅ Initial API pinger created
- ✅ CSV-based data storage
- ✅ 1000+ data points collected

### Day 2 (Jan 4, 2026)
- ✅ Docker setup completed
- ✅ TimescaleDB configured
- ✅ Grafana integrated
- ✅ Database schema designed
- ✅ Git repository initialized

---

## 🤝 Contributing

This is a personal learning project, but suggestions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📚 Learning Resources

**Docker:**
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

**TimescaleDB:**
- [TimescaleDB Docs](https://docs.timescale.com/)
- [Time-Series Best Practices](https://docs.timescale.com/timescaledb/latest/how-to-guides/)

**Grafana:**
- [Grafana Documentation](https://grafana.com/docs/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/)

**Machine Learning:**
- [Anomaly Detection Guide](https://scikit-learn.org/stable/modules/outlier_detection.html)
- [Time-Series Forecasting](https://facebook.github.io/prophet/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built as a learning project to master MLOps and production ML systems
- Inspired by real-world API monitoring challenges
- Special thanks to the open-source community

---

## 📧 Contact

**Your Name** - [@your_twitter](https://twitter.com/your_twitter)

Project Link: [https://github.com/YOUR_USERNAME/api-monitoring-system](https://github.com/YOUR_USERNAME/api-monitoring-system)

---

⭐ **If you find this project interesting, please give it a star!** ⭐
```

**Save this file!**

---

## **STEP 3: CREATE `requirements.txt`**

Create `requirements.txt`:
```
requests==2.31.0
psycopg2-binary==2.9.9
pandas==2.1.4
python-dotenv==1.0.0

# For ML (will add when we get there)
# scikit-learn==1.3.2
# prophet==1.1.5
# statsmodels==0.14.1
```

**Save this file!**

---

## **STEP 4: CREATE `LICENSE` FILE**

Create `LICENSE` file (MIT License):
```
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.