# GOAT Data Analyst - Setup Guide

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database
```bash
python scripts/init_db.py
```

### 6. Run Application
```bash
python main.py
```

## 📁 Project Structure

```
goat_data_analyst/
├── agents/                  # AI agents (Orchestrator, DataLoader, Explorer, etc.)
├── core/                    # Core utilities (Logger, Config, Exceptions)
├── database/                # Database layer (Connection, Models)
├── ui/                      # Frontend (Streamlit)
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── config/                  # Configuration files
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # Project documentation
```

## 🔧 Configuration

### Edit config/config.yml
Customize application settings:
- Database connection
- API host/port
- UI theme
- Agent timeout settings

### Edit .env
Set environment-specific variables:
- APP_DEBUG
- DATABASE_URL
- API_PORT
- UI_THEME

## 📊 Next Steps

### Phase 1: Core Agents (In Progress)
- [ ] DataLoader Agent - CSV/JSON/Excel ingestion
- [ ] Explorer Agent - Descriptive statistics
- [ ] Aggregator Agent - Data aggregation
- [ ] Visualizer Agent - Chart generation

### Phase 2: Advanced Agents
- [ ] Predictor Agent - Time-series forecasting
- [ ] AnomalyDetector Agent - Outlier detection
- [ ] Recommender Agent - Insights extraction
- [ ] Reporter Agent - Report generation

### Phase 3: Integration
- [ ] Database layer implementation
- [ ] REST API endpoints
- [ ] Streamlit UI
- [ ] Testing suite

### Phase 4: Deployment
- [ ] Docker containerization
- [ ] Production deployment
- [ ] Performance optimization
- [ ] Security hardening

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_agents.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## 📝 Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/app.log` (DEBUG level and above)

Log files are rotated when they exceed 10MB.

## 🐛 Troubleshooting

### Virtual Environment Issues
```bash
# Remove and recreate
rmdir /s venv  # Windows
rm -rf venv    # Linux/Mac
python -m venv venv
```

### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
python -c "from database import DatabaseConnection; DatabaseConnection().drop_db()"
python scripts/init_db.py
```

### Import Errors
```bash
# Ensure you're in project root
cd goat_data_analyst
# Verify venv is activated
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## 📚 Resources

- [Build Guide](GOAT_BUILD_GUIDE.md) - Detailed implementation guide
- [Architecture](ARCHITECTURE_GUIDE.md) - System design and components
- [Implementation Checklist](IMPLEMENTATION_CHECKLIST.md) - Step-by-step tasks
- [Quick Reference](QUICK_REFERENCE.md) - Common commands

## 🤝 Development Workflow

1. **Create Branch**: `git checkout -b feature/agent-name`
2. **Implement Feature**: Write code with tests
3. **Run Tests**: `pytest tests/`
4. **Commit**: `git commit -m "Feature: Description"`
5. **Push**: `git push origin feature/agent-name`
6. **Create PR**: GitHub → Create Pull Request

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review existing GitHub issues
3. Create new issue with details

---

**Ready to build? Let's go! 🚀**
