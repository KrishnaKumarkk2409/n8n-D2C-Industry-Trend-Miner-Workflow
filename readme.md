# n8n D2C Industry Trend Miner Workflow

An advanced n8n automation workflow that aggregates, analyzes, and generates insights from Direct-to-Consumer (D2C) industry trends across multiple data sources including news, social media, and custom APIs.

## 🎯 Overview

This workflow automates the complete pipeline for D2C trend analysis:
- **Data Collection**: Fetches from News API, Twitter/X, and custom FastAPI endpoints
- **AI Analysis**: Uses Google Cloud Natural Language and OpenAI for sentiment analysis and theme extraction
- **Intelligence Generation**: Creates structured insights and trend reports
- **Output Generation**: Produces JSON files and Markdown reports

## 📹 Demo Video
<video width="640" height="360" controls>
  <source src="samplevideo.mov" type="video">
  Your browser does not support the video tag.
</video>



## 🏗️ Architecture

The workflow consists of 4 main ETL pipelines:

### 1. News API Pipeline
- Fetches D2C India trends from NewsAPI
- Performs sentiment analysis with Google Cloud NLP
- Structures and normalizes news data

### 2. Twitter/X Pipeline  
- Searches recent tweets for D2C trends
- Analyzes social sentiment
- Extracts social media insights

### 3. Custom API Pipeline
- Integrates with local FastAPI service (port 8000)
- Fetches aggregated multi-source data
- Limits to top 20 trending items

### 4. AI Analysis & Report Generation
- Consolidates all data streams
- Extracts themes using OpenAI GPT-4
- Generates structured insights report

## 🛠️ Prerequisites

### Required Services & APIs

1. **n8n Instance** (v1.0+)
   - Self-hosted or cloud instance
   - LangChain nodes enabled

2. **API Credentials**:
   ```
   - NewsAPI: API key for news data
   - Twitter/X: Bearer token for social data  
   - Google Cloud: Natural Language API credentials
   - OpenAI: API key for GPT-4 analysis
   ```

3. **Local FastAPI Service**:
   ```bash
   # Must be running on localhost:8000
   # See app.py in project directory
   ```

### Dependencies

- **n8n Core Nodes**: HTTP Request, Split Out, Merge, Set, Limit
- **n8n AI Nodes**: LangChain OpenAI, Google Cloud NLP
- **Custom Nodes**: Execute Command, Convert to File

## 📦 Installation

### Step 1: Import Workflow
1. Download the workflow file: `n8n Assignment - D2C Industry Trend Miner.json`
2. In n8n, go to **Workflows** → **Import from file**
3. Select the downloaded JSON file

### Step 2: Configure Credentials

Please Check Temp creds in .env, 
Set up the following credential types in n8n:

#### NewsAPI Credentials
```
Credential Type: HTTP Query Auth
Name: Query Auth account
Query Parameters:
  - apiKey: [YOUR_NEWSAPI_KEY]
```

#### Twitter/X Credentials  
```
Credential Type: HTTP Header Auth
Name: Twitter Bearer
Headers:
  - Authorization: Bearer [YOUR_TWITTER_BEARER_TOKEN]
```

#### Google Cloud NLP
```
Credential Type: Google Cloud Natural Language OAuth2
Name: Google Cloud Natural Language account
Setup: Follow Google Cloud OAuth2 setup
```

#### OpenAI Credentials
```
Credential Type: OpenAI
Name: OpenAi account  
API Key: [YOUR_OPENAI_API_KEY]
```

### Step 3: Start FastAPI Service
```bash
# Navigate to your FastAPI directory
cd /path/to/your/d2c-fastapi
python app.py
# Ensure service runs on http://127.0.0.1:8000
```

### Step 4: Update File Paths
Modify the **Execute Command** node to match your local paths:
```bash
cd /your/path/to/d2c
chmod +x run.sh
./run.sh deps
./run.sh start
```

## ⚙️ Configuration

### Workflow Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `window_days` | 7 | Days to look back for trends |
| `limit` | 50 | Max items per data source |
| `concurrent` | 8 | Concurrent API requests |
| `max_themes` | 5 | Maximum themes to extract |
| `sample_per_theme` | 3 | Evidence samples per theme |

### Seed Themes Configuration
The workflow uses predefined seed themes for analysis:

```json
[
  {
    "name": "Quick commerce adoption in Tier-2 India",
    "keywords": ["quick commerce", "Blinkit", "Zepto", "10-minute", "kirana"]
  },
  {
    "name": "Festival E-commerce Surge", 
    "keywords": ["festive", "sale", "GMV", "ecommerce", "seasonal"]
  },
  {
    "name": "ONDC & Logistics Rail",
    "keywords": ["ONDC", "logistics", "last-mile", "warehousing"] 
  },
  {
    "name": "D2C Funding & M&A",
    "keywords": ["funding", "valuation", "IPO", "VC", "acquisition"]
  },
  {
    "name": "Beauty & Personal Care D2C",
    "keywords": ["beauty", "personal care", "skincare", "ayurveda"]
  }
]
```

## 🚀 Usage

### Manual Execution
1. Open the workflow in n8n
2. Click **"Execute workflow"** button
3. Monitor execution in real-time
4. Download generated files from output nodes




## 📊 Output Files

The workflow generates three key deliverables:

### 1. Items.json
Raw aggregated data from all sources:
```json
{
  "title": "D2C Brand Raises $10M",
  "source": {"name": "techcrunch.com"},
  "author": "Reporter Name",
  "url": "https://example.com/article",
  "publishedAt": "2025-09-22T10:30:00Z",
  "documentSentiment": {
    "magnitude": 2.5,
    "score": 0.8
  }
}
```

### 2. Theme.json  
Structured theme analysis:
```json
{
  "name": "Quick commerce adoption in Tier-2 India",
  "description": "Rapid growth of 10-minute delivery in smaller cities",
  "volume": 15,
  "trajectory": "rising", 
  "tone": 0.65,
  "keywords": ["quick commerce", "Blinkit", "tier-2"],
  "samples": [
    {"title": "...", "source": "...", "url": "..."}
  ]
}
```

### 3. Insight.md
Executive summary report:
```markdown
# D2C — Weekly Trend Insights (last 7 days)

Themes: Quick commerce adoption (rising), Festival E-commerce (steady), D2C Funding (falling)

## 1. Quick commerce adoption in Tier-2 India — Rapid expansion beyond metros
- Why it matters now: 10-minute delivery services expanding to smaller cities
- Key evidence:
  1. Blinkit launches in 50 new cities — Economic Times
  2. Zepto eyes tier-2 expansion — Business Standard  
- Stats: volume=15, trajectory=rising, tone=0.65

...
```


### Modifying AI Prompts
Edit the **AI Agent** node prompt to customize:
- Theme extraction logic
- Sentiment analysis parameters  
- Output format requirements

### Custom Sentiment Lexicon
Modify sentiment keywords in the system prompt:
```
Positive: rise, growth, record, expand, funding, profit
Negative: decline, fall, loss, slowdown, layoff, ban
```

## 📁 File Structure

```
d2c-trend-miner/
├── README.md
├── n8n Assignment - D2C Industry Trend Miner.json
├── app.py                     # FastAPI service
├── run.sh                     # Startup script
├── demo-video.mp4            # Workflow demo
├── Sample outputs/
│   ├── Items.json            # Raw data
│   ├── Theme.json            # Theme analysis  
│   └── insight.md            # Final report
└── Custom_ETL_code_Explanation.md
```

## 🐛 Troubleshooting

### Common Issues

#### Workflow Fails at HTTP Request Nodes
```bash
# Check API credentials
# Verify endpoint URLs are accessible
# Check rate limits
```
#### Twitter/X Rate Limits
```bash
# Try to run flow after some time, as Twitter/ X allows 1 Request/ Minute
```
#### Google Cloud NLP Errors
```bash
# Verify OAuth2 setup
# Check API quotas in Google Cloud Console
# Ensure Natural Language API is enabled
```

#### FastAPI Connection Failed  
```bash
# Verify service is running: curl http://127.0.0.1:8000/health
# Check firewall settings
# Verify port 8000 is available
```

#### OpenAI Rate Limits
```bash
# Reduce concurrent requests
# Implement exponential backoff
# Check API usage limits
```

### Debug Mode
Enable debug logging in workflow settings:
```javascript
Settings → Save Progress → ON
Settings → Timeout → 300 seconds
```

## 📈 Performance Optimization

### Execution Time
- Expected runtime: 3-5 minutes
- Bottlenecks: API rate limits, AI processing
- Optimization: Adjust concurrency settings

### Cost Management
- NewsAPI: 1000 requests/day (free tier)
- OpenAI: ~$0.08 per execution (GPT-4o-mini)
- Google Cloud: 1000 requests (free tier subscription)
- Twitter/ X : 1 Request/ Min (free tier)

### Scaling Considerations
- Use n8n cloud for high availability
- Implement caching for repeated requests
- Consider batch processing for large datasets

## 🔐 Security

### API Key Management
- Use n8n credentials system
- Never hardcode keys in workflow
- Rotate keys regularly

### Data Privacy
- All processing happens in your n8n instance
- No data stored in external services
- Configure data retention policies

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Test changes thoroughly
4. Submit pull request

### Testing Checklist
- [ ] All API credentials configured
- [ ] FastAPI service running
- [ ] Workflow executes successfully  
- [ ] Output files generated correctly
- [ ] No sensitive data in outputs

## 📄 License

This n8n workflow is released under the MIT License.

```
Copyright (c) 2025 Krishna Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

## 📞 Support

### Getting Help
- **Issues**: Create GitHub issue with workflow logs
- **Questions**: Check n8n community forum
- **Custom Development**: Contact krishnakumar.kk2409@gmail.com

### Documentation Links

- [FastAPI Integration Guide](Custom_ETL_code_Explanation.md)

---

**Last Updated**: September 2025  
**Workflow Version**: 1.0.0  
**Compatible n8n Version**: 1.0+