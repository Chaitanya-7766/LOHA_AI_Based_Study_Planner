# 🚀 QUICK START - LOHA Chatbot with Groq API

## 5-Minute Setup

### Step 1: Get API Key (2 minutes)
```
1. Go to https://console.groq.com
2. Sign up (free)
3. Get your API key
4. Copy the key
```

### Step 2: Set Environment Variable (1 minute)
**Pick ONE method:**

**macOS/Linux Terminal:**
```bash
export GROQ_API_KEY="your_api_key_here"
```

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

**Or create `.streamlit/secrets.toml`:**
```toml
GROQ_API_KEY = "your_api_key_here"
GROQ_MODEL = "llama-3.1-8b-instant"
```

### Step 3: Start App (1 minute)
```bash
streamlit run app.py
```

### Step 4: Test (1 minute)
1. Click **AI Chatbot** in sidebar
2. Click any quick question button
3. Wait for 🤔 spinner
4. See AI response!

## ✅ What Works

- ✅ User sends message
- ✅ Groq AI processes it with your study profile context
- ✅ Smart responses about studying tailored to YOU
- ✅ Messages saved to database
- ✅ Chat history preserved
- ✅ Works on AI Chatbot page AND floating chatbot

## 🎯 Example Questions to Ask

- "How to study ML?" 
- "I'm weak in algorithms, help me"
- "Make me an exam prep plan"
- "How to stay motivated?"
- "Best way to use Pomodoro?"

## 🆘 If It Doesn't Work

**Error: "No Groq API key found"**
→ Set `GROQ_API_KEY` environment variable

**Error: "Groq API Error"**  
→ Check your API key at https://console.groq.com

**No response / Timeout**
→ Check internet connection, try again

## 📚 Full Docs

- `GROQ_SETUP.md` - Detailed setup guide
- `IMPLEMENTATION_SUMMARY.md` - What changed in code

## 💡 Pro Tips

1. **Free tier** has rate limits (100 req/day) - fine for testing
2. **llama-3.1-8b-instant** = fastest model
3. **API key = SECRET** - never share or commit to git
4. Your **profile + subjects** improve response quality

---

**That's it! Your chatbot is now AI-powered. 🎉**
