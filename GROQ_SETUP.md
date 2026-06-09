# LOHA Chatbot - Groq API Setup Guide

## Overview
Your AI chatbot is now powered by **Groq API**! This enables intelligent, context-aware responses based on your study profile.

## 📋 Setup Steps

### 1. Get a Groq API Key
1. Visit [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** section
4. Create a new API key and copy it

### 2. Set Environment Variable

**Option A: Using `.streamlit/secrets.toml` (Recommended for Streamlit Cloud)**
```bash
# Create/edit .streamlit/secrets.toml in your project root
GROQ_API_KEY = "your_api_key_here"
GROQ_MODEL = "llama-3.1-8b-instant"  # Optional, defaults to this
```

**Option B: Using System Environment Variable**
```bash
# macOS/Linux
export GROQ_API_KEY="your_api_key_here"

# Windows (PowerShell)
$env:GROQ_API_KEY="your_api_key_here"
```

**Option C: Using `.env` file (if using python-dotenv)**
```bash
# Create .env file in project root
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### 3. Available Groq Models
You can use different models by setting `GROQ_MODEL` environment variable:
- `llama-3.1-8b-instant` (fast, lightweight) - **DEFAULT**
- `mixtral-8x7b-32768` (powerful)
- `llama-3.1-70b-versatile` (advanced)

## 🎯 Features

### Main Chatbot (`pages_loha/chatbot.py`)
- ✅ **Real-time AI responses** using Groq API
- ✅ **Smart context** based on your profile (name, exam date, subjects, study hours)
- ✅ **Chat history** stored in Supabase
- ✅ **Quick action buttons** for common questions
- ✅ **Error handling** with helpful fallback messages

### Floating Chatbot (`pages_loha/floating_chatbot.py`)
- ✅ **Fixed position widget** for quick access anywhere
- ✅ Also uses Groq API with the same features

## 🔧 How It Works

### Flow
```
User Input
    ↓
add to session_state
    ↓
prompt Groq API
    ↓
get AI response
    ↓
save to database
    ↓
display in UI
```

### System Prompt
The chatbot is configured with:
- **Role**: Study assistant focused on practical advice
- **Context**: Student profile, subjects, study goals
- **Response Style**: Concise, actionable, encouraging
- **Max tokens**: 512 (keeps responses brief)

## ✅ Verification

To verify your setup is working:

```python
import os
import urllib.request
import json

api_key = os.getenv("GROQ_API_KEY")
if api_key:
    print("✅ API Key found!")
else:
    print("❌ API Key not found. Set GROQ_API_KEY environment variable.")
```

Run your Streamlit app:
```bash
streamlit run app.py
```

Test the chatbot:
1. Go to **AI Chatbot** page
2. Click one of the **Quick Questions** buttons
3. You should see "🤔 LOHA is thinking..." followed by an AI response

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No Groq API key found" | Set `GROQ_API_KEY` environment variable |
| "Groq API Error" | Check API key validity at [console.groq.com](https://console.groq.com) |
| Rate limit error | Free tier has limits; upgrade plan if needed |
| Timeout error | Groq API unreachable; check internet, try again |
| Empty responses | Model may be overloaded; try a different model |

## 📦 Dependencies

All required libraries are already in `requirements.txt`:
- `streamlit` - Web framework
- `urllib` - HTTP requests (built-in, no install needed)
- `json` - JSON parsing (built-in)

## 🚀 Next Steps

1. ✅ Set up your Groq API key
2. ✅ Test the chatbot with a quick question
3. ✅ Customize the system prompt in `ask_groq()` function if needed
4. ✅ Monitor API usage at [Groq Console](https://console.groq.com)

## 💡 Tips

- **For testing**: Use `llama-3.1-8b-instant` model (fastest)
- **For quality**: Use `mixtral-8x7b-32768` (more capable)
- **Keep API key secret**: Never commit `.env` or `secrets.toml` to version control
- **Monitor usage**: Free tier has rate limits, track your API calls

## 🆘 Support

If problems persist:
1. Check that API key is correctly set: `echo $GROQ_API_KEY` (macOS/Linux)
2. Verify internet connection
3. Check [Groq status page](https://status.groq.com)
4. Review error messages in Streamlit terminal output

**Happy studying! 🧠📚**
