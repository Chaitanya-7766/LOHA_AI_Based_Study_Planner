import re
import string
from collections import Counter

# ── Lightweight NLP without heavy models ──────────────────────────────────────
# Uses regex + NLTK stopwords (falls back to hardcoded if NLTK unavailable)

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","up","about","into","through","during","is","are","was",
    "were","be","been","being","have","has","had","do","does","did","will",
    "would","could","should","may","might","shall","can","need","dare",
    "this","that","these","those","it","its","i","we","you","he","she","they",
    "them","their","our","your","his","her","my","as","if","then","than",
    "so","yet","both","either","neither","each","few","more","most","other",
    "some","such","no","nor","not","only","same","too","very","just","how",
    "what","which","who","whom","when","where","why","all","unit","module",
    "chapter","topic","section","introduction","overview","part","lecture"
}

SUBJECT_KEYWORDS = {
    "Data Structures": ["array","linked list","stack","queue","tree","graph","heap","hash","sorting","searching"],
    "Algorithms": ["algorithm","complexity","big o","dynamic programming","greedy","backtracking","divide and conquer"],
    "Machine Learning": ["regression","classification","clustering","neural network","svm","decision tree","random forest","gradient"],
    "Python": ["python","function","class","object","module","list","dict","tuple","exception","file"],
    "Database": ["sql","database","table","query","join","index","normalization","transaction","er diagram"],
    "Networks": ["tcp","ip","protocol","network","routing","firewall","dns","http","socket","osi"],
    "Operating Systems": ["process","thread","scheduling","memory","deadlock","semaphore","file system","paging"],
    "Mathematics": ["calculus","integral","derivative","matrix","vector","probability","statistics","linear algebra"],
}


def parse_syllabus(text: str) -> dict:
    """
    Parses raw syllabus text into structured topics with difficulty scores.
    Returns {detected_subject, topics: [{name, difficulty_score, keywords}]}
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    topics = []
    
    for line in lines:
        # Skip very short lines or pure headers
        if len(line) < 4:
            continue
        # Clean line
        clean = re.sub(r"^[\d\.\-\*\•\→]+\s*", "", line)  # remove bullets/numbers
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean or len(clean) < 5:
            continue
        # Score difficulty
        diff = _score_difficulty(clean)
        kws = _extract_keywords(clean)
        topics.append({
            "name": clean[:80],
            "difficulty_score": diff,
            "keywords": kws,
            "priority": "High" if diff >= 3.5 else ("Medium" if diff >= 2.5 else "Low")
        })

    detected = _detect_subject(text)

    return {
        "detected_subject": detected,
        "topics": topics,
        "total_topics": len(topics),
        "high_priority": sum(1 for t in topics if t["priority"] == "High"),
        "medium_priority": sum(1 for t in topics if t["priority"] == "Medium"),
        "low_priority": sum(1 for t in topics if t["priority"] == "Low"),
    }


def _score_difficulty(text: str) -> float:
    text_lower = text.lower()
    hard_words = ["advanced","complex","theorem","proof","algorithm","optimization",
                  "differential","integration","quantum","neural","transformer",
                  "concurrency","distributed","cryptography","compilation"]
    medium_words = ["implement","design","analyze","compare","evaluate","develop",
                    "construct","formulate","calculate","derive"]
    easy_words = ["introduction","basic","simple","overview","define","list","name"]

    score = 2.0
    for w in hard_words:
        if w in text_lower: score += 0.5
    for w in medium_words:
        if w in text_lower: score += 0.3
    for w in easy_words:
        if w in text_lower: score -= 0.3

    # Length heuristic — longer topic names tend to be more complex
    if len(text) > 60: score += 0.3

    return round(min(max(score, 1.0), 5.0), 1)


def _extract_keywords(text: str) -> list:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS][:5]


def _detect_subject(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        scores[subject] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


def extract_topics_from_pdf_text(text: str) -> list:
    """Quick extract of topic names from PDF-extracted text."""
    result = parse_syllabus(text)
    return result["topics"]


def generate_topic_summary(topic_name: str) -> str:
    """Rule-based brief description for a topic."""
    topic_lower = topic_name.lower()
    if "sort" in topic_lower:
        return "Sorting algorithms arrange data in a specific order. Key algorithms: Bubble, Merge, Quick Sort."
    elif "tree" in topic_lower:
        return "Tree data structure with hierarchical nodes. Includes BST, AVL, B-Tree variants."
    elif "neural" in topic_lower or "deep" in topic_lower:
        return "Neural networks mimic brain neurons using layers of connected nodes for learning patterns."
    elif "regression" in topic_lower:
        return "Regression predicts continuous output values from input features using statistical modeling."
    elif "sql" in topic_lower or "database" in topic_lower:
        return "Structured Query Language for managing relational databases with CRUD operations."
    elif "os" in topic_lower or "operating" in topic_lower:
        return "OS manages hardware resources, processes, memory, and file systems for applications."
    else:
        return f"Study this topic carefully. Focus on core concepts, definitions, and practical applications."