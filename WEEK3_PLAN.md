# 📖 WEEK 3: Narrative Generator

**Goal:** Make results understandable to non-technical users  
**Hours:** 40h | **Tests:** +30 | **Score:** 8.9/10

## Why Week 3?
Without narrative, you have:
- Raw numbers
- Anomalies detected
- Predictions made

But users don't know:
- **"What does this mean?"**
- **"What should I do about it?"**
- **"Where are my problems?"**

Narrative generator answers these questions.

## Architecture

```
agents/narrative_generator/
├── narrative_generator.py      ← Orchestrator
└── workers/
    ├── insight_extractor.py    ← Extract key stats
    ├── problem_identifier.py   ← What's wrong?
    ├── action_recommender.py   ← What to do?
    └── story_builder.py        ← Build narrative text
```

## Daily Breakdown

### Day 11 (Fri, Dec 20) - Insight Extractor (8h)
**Focus:** Pull key findings from agent results

**Build:**
- Parse anomaly detector results → extract key anomalies
- Parse predictor results → extract accuracy/confidence
- Parse recommender results → extract top recommendations
- Parse reporter results → extract statistics
- Score importance of each insight

**Code Example:**
```python
class InsightExtractor:
    def extract_anomalies(self, results):
        # Returns: {count, severity, top_anomalies, % of data}
        
    def extract_predictions(self, results):
        # Returns: {accuracy, confidence, top_features, trend}
        
    def extract_recommendations(self, results):
        # Returns: {top_3_actions, confidence, data_issues}
```

**Tests:**
```
✓ Extract key anomalies from results
✓ Calculate anomaly percentage
✓ Extract prediction accuracy
✓ Extract feature importance
✓ Extract top 3 recommendations
✓ Score insight importance
✓ Handle missing results gracefully
✓ Validation: scores 0-1 scale
```

**Success Criteria:**
- [ ] 8+ tests passing
- [ ] All agent result types parsed
- [ ] Key insights extracted accurately

---

### Day 12 (Sat, Dec 21) - Problem Identifier (8h)
**Focus:** Identify what's wrong with the data

**Build:**
- Classify problems: anomalies, missing data, low predictions, bad distributions
- Rank by severity (critical, high, medium, low)
- Explain impact of each problem
- Suggest which to fix first

**Code Example:**
```python
class ProblemIdentifier:
    def identify_problems(self, results):
        # Returns: [{type, severity, description, impact, location}]
        
        problems = []
        
        # Problem 1: Anomalies
        if results['anomalies']['count'] > threshold:
            problems.append({
                'type': 'anomaly',
                'severity': 'high',
                'count': results['anomalies']['count'],
                'description': f"{count} unusual values detected",
                'impact': 'Skews averages, affects predictions'
            })
        
        # Problem 2: Missing data
        # Problem 3: Poor predictions
        # Problem 4: Outliers
        
        return sorted(problems, key=lambda x: severity_score(x['severity']))
```

**Tests:**
```
✓ Detect anomalies as problem
✓ Detect missing data as problem
✓ Detect low prediction confidence as problem
✓ Severity scoring: critical > high > medium > low
✓ Multiple problems identified and ranked
✓ Impact descriptions are helpful
✓ Handle clean datasets (no problems)
✓ Validate problem structure
```

**Success Criteria:**
- [ ] 8+ tests passing
- [ ] Problems correctly identified and ranked
- [ ] Impact descriptions are clear

---

### Day 13 (Sun, Dec 22) - Action Recommender (8h)
**Focus:** Tell users what to do

**Build:**
- For each problem, generate actionable recommendations
- Rank by priority and impact
- Explain why the action matters
- Provide next steps

**Code Example:**
```python
class ActionRecommender:
    def recommend_actions(self, problems):
        # Returns: [{priority, action, detail, impact}]
        
        actions = []
        
        for problem in problems:
            if problem['type'] == 'anomaly':
                actions.append({
                    'priority': problem['severity'],
                    'action': 'Investigate anomalies',
                    'detail': f"Found {problem['count']} unusual values. "
                             f"Investigate {problem['location']} first.",
                    'impact': 'Improves model accuracy by ~5%'
                })
            elif problem['type'] == 'missing_data':
                actions.append({
                    'priority': 'high',
                    'action': 'Handle missing data',
                    'detail': f"Fill {problem['%']}% missing values or exclude rows",
                    'impact': 'Improves data completeness from {old}% to {new}%'
                })
        
        return sorted(actions, key=priority_score)
```

**Tests:**
```
✓ Anomaly problem → investigation action
✓ Missing data problem → handling action
✓ Low prediction problem → data improvement action
✓ Actions are prioritized correctly
✓ Actions are specific (not generic)
✓ Impact is quantified when possible
✓ Multiple actions for multiple problems
✓ Handle edge cases (no problems)
```

**Success Criteria:**
- [ ] 8+ tests passing
- [ ] Actions are specific and actionable
- [ ] Priorities are correct

---

### Day 14 (Mon, Dec 23) - Story Builder (8h)
**Focus:** Combine insights into readable narrative

**Build:**
- Combine insights + problems + actions into narrative
- Write in plain English (non-technical)
- Structure: headline → summary → problems → actions → next steps
- Output as JSON object

**Code Example:**
```python
class StoryBuilder:
    def build_narrative(self, insights, problems, actions):
        # Returns: {headline, summary, problems, actions, next_steps}
        
        return {
            'headline': f"Your data shows {insights['anomaly_count']} "
                       f"anomalies and {insights['prediction_accuracy']}% "
                       f"prediction confidence",
            
            'summary': f"Your dataset contains {insights['rows']} records. "
                      f"We found {len(problems)} issues and {len(actions)} "
                      f"recommendations to improve data quality.",
            
            'problems': problems,
            'actions': actions,
            
            'next_steps': [
                f"1. {actions[0]['action'].lower()}",
                f"2. {actions[1]['action'].lower() if len(actions) > 1 else '...'}"
            ],
            
            'confidence': self._calculate_narrative_confidence(insights)
        }
```

**Output Example:**
```json
{
  "headline": "Your data shows 23 anomalies and 87% prediction confidence",
  "summary": "Your dataset contains 10,000 records. We found 3 issues and 5 recommendations to improve data quality.",
  "problems": [
    {
      "type": "anomaly",
      "severity": "high",
      "description": "23 transactions exceed normal patterns by 5x",
      "location": "Region: North, Dec 10",
      "impact": "Skews average sales by 12%"
    }
  ],
  "actions": [
    {
      "priority": "high",
      "action": "Investigate anomalies",
      "detail": "23 unusual values found. Focus on North region Dec 10.",
      "impact": "Improves accuracy by ~5%"
    }
  ],
  "next_steps": [
    "1. Investigate the North region spike on Dec 10",
    "2. Fill missing Q1 data or exclude from training",
    "3. Consider holiday seasonality in your forecasts"
  ]
}
```

**Tests:**
```
✓ Narrative includes headline
✓ Narrative includes summary
✓ Narrative includes problems
✓ Narrative includes actions
✓ Narrative includes next steps
✓ Headline is engaging but accurate
✓ Summary mentions key numbers
✓ Actions are in priority order
✓ Language is non-technical
✓ JSON structure is valid
```

**Success Criteria:**
- [ ] 8+ tests passing
- [ ] Narratives are clear and helpful
- [ ] Structure is consistent

---

### Day 15 (Tue, Dec 24) - Integration + Testing (8h)
**Focus:** Full narrative pipeline working

**Build:**
- Integrate narrative generator into orchestrator
- Narrative is part of /analyze response
- Test with real data scenarios
- Validate narratives are accurate

**Tests:**
```
✓ Orchestrator → Narrative Generator → Combined result
✓ Dataset with anomalies: narrative identifies them
✓ Dataset with missing data: narrative identifies it
✓ Dataset all clean: narrative says "data looks good"
✓ Narrative for quick pipeline vs full pipeline
✓ Performance: narrative generation < 1s
✓ Narrative survives large datasets (100K rows)
✓ Multiple scenarios tested (10+ datasets)
```

**Success Criteria:**
- [ ] 8+ tests passing
- [ ] Narrative generator integrated
- [ ] Narratives accurate on test data
- [ ] Performance maintained

---

### Week 3 Exit Criteria ✅
- ✅ Narrative generator fully functional
- ✅ 30+ new tests (insight, problem, action, story, integration)
- ✅ 214 total tests passing (184 + 30)
- ✅ Users get clear guidance on their data
- ✅ **Score: 8.9/10** (User-Friendly)
