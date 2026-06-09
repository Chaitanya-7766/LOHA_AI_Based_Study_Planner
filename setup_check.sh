#!/bin/bash
# LOHA Chatbot Setup Checklist

echo "🚀 LOHA Chatbot - Quick Setup"
echo "=============================="
echo ""

# Step 1: Check API Key
echo "1️⃣ Checking Groq API Key..."
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY not set"
    echo "   Set it with: export GROQ_API_KEY='your_key_here'"
else
    echo "✅ GROQ_API_KEY is set"
fi
echo ""

# Step 2: Python version
echo "2️⃣ Checking Python version..."
python --version
echo ""

# Step 3: Check Streamlit
echo "3️⃣ Checking Streamlit..."
pip list | grep streamlit || echo "❌ Streamlit not installed"
echo ""

# Step 4: Check required files
echo "4️⃣ Checking files..."
files=(
    "app.py"
    "pages_loha/chatbot.py"
    "pages_loha/floating_chatbot.py"
    "db.py"
    "requirements.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file not found"
    fi
done
echo ""

# Step 5: Ready to test
echo "5️⃣ Ready to test?"
echo "   Run: streamlit run app.py"
echo "   Then navigate to 'AI Chatbot' page"
echo ""

echo "📚 For detailed setup, see: GROQ_SETUP.md"
