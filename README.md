# GOAT Data Analyst 🐐

An AI-powered data analysis system with 9 specialized agents for comprehensive data exploration, visualization, and insights.

## Project Structure

```
goat_data_analyst/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── orchestrator.py    # Master coordinator
│   ├── data_loader.py     # Data ingestion
│   ├── explorer.py        # Data exploration
│   ├── aggregator.py      # Statistical aggregation
│   ├── visualizer.py      # Chart generation
│   ├── predictor.py       # ML predictions
│   ├── anomaly_detector.py# Outlier detection
│   ├── recommender.py     # Data insights
│   └── reporter.py        # Report generation
├── core/                   # Core utilities
│   ├── __init__.py
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging
│   └── exceptions.py      # Custom exceptions
├── database/              # Database layer
│   ├── __init__.py
│   ├── connection.py      # DB connection
│   ├── models.py          # SQLAlchemy models
│   └── migrations/        # Alembic migrations
├── ui/                    # Frontend (Streamlit)
│   ├── __init__.py
│   ├── main.py           # Main app
│   ├── pages/            # Multi-page UI
│   ├── components/       # Reusable components
│   └── styles/           # CSS/styling
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_database.py
│   └── test_integration.py
├── config/                # Configuration files
│   ├── config.yml
│   └── secrets.yml.example
├── scripts/               # Utility scripts
│   ├── init_db.py
│   └── seed_data.py
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── main.py               # Entry point
```

## Quick Start

1. **Setup**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate  # Windows
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

3. **Run Application**
   ```bash
   python main.py
   ```

## Agents Overview

| Agent | Purpose |
|-------|----------|
| Orchestrator | Coordinates all agents & manages workflow |
| Data Loader | Ingests CSV, JSON, SQL data |
| Explorer | Generates descriptive statistics |
| Aggregator | Computes summaries & groupings |
| Visualizer | Creates interactive charts |
| Predictor | Time-series & ML predictions |
| Anomaly Detector | Identifies outliers |
| Recommender | Extracts actionable insights |
| Reporter | Generates formatted reports |

## Status

- [x] Documentation
- [ ] Project Structure Setup
- [ ] Agent Development
- [ ] Database Layer
- [ ] UI/Frontend
- [ ] Testing
- [ ] Deployment

## License

MIT
