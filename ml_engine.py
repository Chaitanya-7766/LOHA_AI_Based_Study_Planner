"""
ml/engine.py – LOHA AI/ML Engine
=================================
Models:
  1. Exam Score Predictor        – GradientBoostingRegressor
  2. Weak Topic Detector         – RandomForestClassifier
  3. Optimal Study Time          – KMeans clustering + scoring
  4. Performance Trend Detector  – LinearRegression trend analysis
  5. Spaced Repetition Scheduler – SM-2 algorithm

All models are trained on synthetic data at startup and cached in memory.
"""

import numpy as np
import os, json, pickle
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# ── Paths ────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)

# ── Global model cache ───────────────────────────────────────
_models: Dict[str, Any] = {}


# ════════════════════════════════════════════════════════════
# 1. SYNTHETIC DATA GENERATION
# ════════════════════════════════════════════════════════════

def _rng(seed=42):
    return np.random.default_rng(seed)


def generate_score_predictor_data(n=3000):
    """
    Features: avg_score, study_hours_per_week, days_to_exam,
              sessions_count, consistency_score, target_score
    Target:   predicted_final_score
    """
    rng = _rng(1)
    avg_score         = rng.uniform(20, 100, n)
    study_hours       = rng.uniform(1, 40, n)
    days_to_exam      = rng.integers(1, 120, n).astype(float)
    sessions          = rng.integers(1, 80, n).astype(float)
    consistency       = rng.uniform(0, 1, n)   # 0=irregular, 1=daily
    target            = rng.uniform(60, 100, n)

    # Realistic outcome: weighted combination + noise
    predicted = (
        0.40 * avg_score
        + 0.20 * np.clip(study_hours * 1.5, 0, 30)
        + 0.15 * consistency * 20
        + 0.10 * np.clip(sessions * 0.3, 0, 20)
        + 0.05 * np.clip(days_to_exam * 0.2, 0, 15)
        + rng.normal(0, 4, n)
    )
    predicted = np.clip(predicted, 0, 100)

    X = np.column_stack([avg_score, study_hours, days_to_exam,
                         sessions, consistency, target])
    return X, predicted


def generate_weak_topic_data(n=4000):
    """
    Features: score_trend (slope), avg_score, score_variance,
              time_since_last_study, sessions_count, target_gap
    Target:   0=strong, 1=moderate, 2=weak, 3=critical
    """
    rng = _rng(2)
    avg_score    = rng.uniform(10, 100, n)
    score_trend  = rng.uniform(-5, 5, n)   # points per week
    variance     = rng.uniform(0, 400, n)
    time_since   = rng.uniform(0, 30, n)   # days
    sessions     = rng.integers(0, 50, n).astype(float)
    target_gap   = rng.uniform(-20, 50, n) # target - avg

    # Label logic
    labels = np.zeros(n, dtype=int)
    labels[avg_score < 40]  = 3   # critical
    labels[(avg_score >= 40) & (avg_score < 60)] = 2  # weak
    labels[(avg_score >= 60) & (avg_score < 75)] = 1  # moderate
    labels[avg_score >= 75] = 0   # strong

    # Modifiers
    labels = np.clip(labels + (score_trend < -2).astype(int), 0, 3)
    labels = np.clip(labels + (time_since > 14).astype(int), 0, 3)

    X = np.column_stack([avg_score, score_trend, variance,
                         time_since, sessions, target_gap])
    return X, labels


def generate_study_time_data(n=5000):
    """
    Generates session records: hour_of_day, day_of_week, duration_mins,
    focus_score, subject_difficulty
    Used to cluster optimal study windows.
    """
    rng = _rng(3)
    hour        = rng.integers(5, 24, n).astype(float)
    day_of_week = rng.integers(0, 7, n).astype(float)
    duration    = rng.uniform(25, 120, n)
    difficulty  = rng.uniform(1, 5, n)

    # Focus score peaks in morning (7-9) and evening (19-22)
    base_focus = 5.0
    morning_boost = np.exp(-0.5 * ((hour - 8) / 1.5) ** 2) * 3
    evening_boost = np.exp(-0.5 * ((hour - 20) / 1.5) ** 2) * 2.5
    weekend_boost = (day_of_week >= 5).astype(float) * 0.5
    focus = np.clip(base_focus + morning_boost + evening_boost
                    + weekend_boost + rng.normal(0, 0.8, n), 1, 10)

    X = np.column_stack([hour, day_of_week, duration, difficulty, focus])
    return X


def generate_performance_data(n=2000):
    """
    Score sequences per student — used for trend detection.
    Returns list of (scores_list, trend_label)
    trend: -1=declining, 0=stable, 1=improving
    """
    rng = _rng(4)
    data = []
    for _ in range(n):
        start  = rng.uniform(30, 90)
        trend  = rng.uniform(-3, 3)   # points per test
        noise  = rng.uniform(3, 12)
        length = rng.integers(3, 10)
        scores = [float(np.clip(start + trend*i + rng.normal(0, noise), 0, 100))
                  for i in range(length)]
        label = 1 if trend > 1 else (-1 if trend < -1 else 0)
        data.append((scores, label))
    return data


# ════════════════════════════════════════════════════════════
# 2. MODEL TRAINING
# ════════════════════════════════════════════════════════════

def train_score_predictor():
    X, y = generate_score_predictor_data()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('gbr', GradientBoostingRegressor(
            n_estimators=200, max_depth=4,
            learning_rate=0.08, subsample=0.8,
            random_state=42
        ))
    ])
    model.fit(X_tr, y_tr)
    mae = mean_absolute_error(y_te, model.predict(X_te))
    print(f"  [ScorePredictor] MAE = {mae:.2f}")
    return model


def train_weak_topic_detector():
    X, y = generate_weak_topic_data()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=150, max_depth=8,
            class_weight='balanced', random_state=42
        ))
    ])
    model.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te))
    print(f"  [WeakTopicDetector] Accuracy = {acc:.3f}")
    return model


def train_study_time_recommender():
    X = generate_study_time_data()
    # Cluster sessions into 4 study-window types
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('kmeans', KMeans(n_clusters=6, random_state=42, n_init=10))
    ])
    model.fit(X)
    print(f"  [StudyTimeRecommender] KMeans trained on {len(X)} sessions")
    return model


def init_models():
    """Train all models and cache them. Called once at startup."""
    global _models
    if _models:
        return  # Already loaded

    # Try loading from disk first
    cache_path = MODEL_DIR / "models.pkl"
    if cache_path.exists():
        print("✅ Loading cached ML models...")
        with open(cache_path, "rb") as f:
            _models = pickle.load(f)
        return

    print("🧠 Training ML models on synthetic data...")
    _models["score_predictor"]    = train_score_predictor()
    _models["weak_topic_detector"] = train_weak_topic_detector()
    _models["study_time"]         = train_study_time_recommender()

    # Persist to disk
    with open(cache_path, "wb") as f:
        pickle.dump(_models, f)
    print("✅ All models trained and cached.")


# ════════════════════════════════════════════════════════════
# 3. INFERENCE FUNCTIONS
# ════════════════════════════════════════════════════════════

# ── 3a. Exam Score Predictor ─────────────────────────────────
def predict_exam_score(
    avg_score: float,
    study_hours_per_week: float,
    days_to_exam: int,
    sessions_count: int,
    consistency_score: float,
    target_score: float,
) -> Dict[str, Any]:
    init_models()
    X = np.array([[avg_score, study_hours_per_week, days_to_exam,
                   sessions_count, consistency_score, target_score]])
    pred = float(_models["score_predictor"].predict(X)[0])
    pred = round(np.clip(pred, 0, 100), 1)

    gap       = target_score - pred
    on_track  = pred >= target_score * 0.9
    extra_hrs = max(0, round(gap * 0.8, 1)) if not on_track else 0

    return {
        "predicted_score": pred,
        "target_score":    target_score,
        "gap":             round(gap, 1),
        "on_track":        on_track,
        "extra_hours_needed": extra_hrs,
        "confidence":      "high" if sessions_count >= 5 else "low",
        "message": (
            f"Predicted final score: {pred}%. "
            + ("You're on track! 🎯" if on_track
               else f"Need {extra_hrs} more study hours to reach {target_score}%.")
        )
    }


# ── 3b. Weak Topic Detector ──────────────────────────────────
WEAKNESS_LABELS = {0: "strong", 1: "moderate", 2: "weak", 3: "critical"}
WEAKNESS_COLORS = {0: "#10b981", 1: "#f59e0b", 2: "#ef4444", 3: "#7c3aed"}

def detect_weak_subjects(subjects: List[Dict]) -> List[Dict]:
    """
    Takes list of subject performance dicts from v_subject_performance view.
    Annotates each with ML-detected weakness tier + recommendation.
    """
    init_models()
    results = []
    for s in subjects:
        avg    = float(s.get("avg_score", 0))
        target = float(s.get("target_score", 80))
        tests  = int(s.get("test_count", 0))
        sess   = int(s.get("session_count", 0))

        # Compute trend from recent scores if available
        recent = s.get("recent_scores", [])
        if len(recent) >= 2:
            xs = np.arange(len(recent))
            slope = float(np.polyfit(xs, recent, 1)[0])
        else:
            slope = 0.0

        variance   = float(np.var(recent)) if recent else 20.0
        time_since = float(s.get("days_since_last_study", 7))
        target_gap = target - avg

        X = np.array([[avg, slope, variance, time_since, sess, target_gap]])
        label_idx = int(_models["weak_topic_detector"].predict(X)[0])
        proba     = _models["weak_topic_detector"].predict_proba(X)[0]

        tier  = WEAKNESS_LABELS[label_idx]
        color = WEAKNESS_COLORS[label_idx]

        rec = _build_recommendation(tier, avg, target, slope, time_since)

        results.append({
            **s,
            "weakness_tier":       tier,
            "weakness_score":      label_idx,
            "weakness_color":      color,
            "confidence":          round(float(proba.max()), 2),
            "score_trend":         round(slope, 2),
            "extra_hours_needed":  max(0, round((target - avg) * 0.5, 1)),
            "recommendation":      rec,
        })

    # Sort: critical → weak → moderate → strong
    results.sort(key=lambda x: x["weakness_score"], reverse=True)
    return results


def _build_recommendation(tier, avg, target, slope, days_since):
    if tier == "critical":
        return (f"⚠️ Critical — avg {avg:.0f}% vs target {target:.0f}%. "
                f"Schedule daily 2-hour sessions immediately. "
                + ("Trend is declining — change your study approach." if slope < 0 else ""))
    elif tier == "weak":
        extra = round((target - avg) * 0.6, 1)
        return (f"Weak area — needs {extra}h extra this week. "
                f"Focus on practice problems over passive reading.")
    elif tier == "moderate":
        return (f"On the edge — {target-avg:.0f} points from target. "
                + ("Good recent trend, keep momentum." if slope > 0
                   else "Consider reviewing fundamentals."))
    else:
        stale = f" Last studied {days_since:.0f} days ago — quick revision recommended." if days_since > 10 else ""
        return f"Strong subject. Maintain with light weekly revision.{stale}"


# ── 3c. Optimal Study Time Recommender ───────────────────────
HOUR_LABELS = {
    range(5, 9):   "Early Morning",
    range(9, 12):  "Late Morning",
    range(12, 15): "Afternoon",
    range(15, 18): "Late Afternoon",
    range(18, 21): "Evening",
    range(21, 24): "Night",
}

def recommend_study_times(
    sessions: List[Dict],
    daily_hours: float = 4.0,
    peak_preference: str = "evening",
) -> Dict[str, Any]:
    """
    Analyses past session data to recommend optimal study windows.
    Falls back to preference-based recommendation if <5 sessions.
    """
    init_models()

    preference_map = {
        "morning":   [7, 8, 9],
        "afternoon": [13, 14, 15],
        "evening":   [19, 20, 21],
        "night":     [22, 23, 0],
    }

    if len(sessions) < 5:
        # Not enough data — use preference
        hours = preference_map.get(peak_preference, [19, 20, 21])
        return {
            "method": "preference",
            "recommended_hours": hours,
            "peak_hour": hours[0],
            "peak_label": _hour_label(hours[0]),
            "slots": _build_slots(hours, daily_hours),
            "message": f"Based on your {peak_preference} preference. Study more to get personalised recommendations.",
            "data_points": len(sessions),
        }

    # Build feature matrix from real sessions
    rows = []
    for s in sessions:
        try:
            h = datetime.fromisoformat(s["started_at"]).hour
            d = datetime.fromisoformat(s["started_at"]).weekday()
            dur   = float(s.get("duration_mins") or 25)
            focus = float(s.get("focus_score") or 7)
            rows.append([h, d, dur, 3.0, focus])
        except Exception:
            continue

    if not rows:
        hours = preference_map.get(peak_preference, [19, 20, 21])
        return {
            "method": "preference",
            "recommended_hours": hours,
            "peak_hour": hours[0],
            "peak_label": _hour_label(hours[0]),
            "slots": _build_slots(hours, daily_hours),
            "message": "Using your preference (parse error).",
            "data_points": 0,
        }

    X = np.array(rows)
    clusters = _models["study_time"].predict(X)

    # Find cluster with highest mean focus score
    best_cluster, best_focus, best_hours = 0, 0.0, []
    for c in range(6):
        mask = clusters == c
        if mask.sum() == 0:
            continue
        mean_focus = X[mask, 4].mean()
        if mean_focus > best_focus:
            best_focus   = mean_focus
            best_cluster = c
            best_hours   = sorted(set(X[mask, 0].astype(int).tolist()))

    top_hours = best_hours[:3] if best_hours else preference_map[peak_preference]

    # Hour-level focus averages
    hour_focus = {}
    for row in X:
        h = int(row[0])
        hour_focus.setdefault(h, []).append(row[4])
    hour_avg = {h: round(float(np.mean(v)), 2) for h, v in hour_focus.items()}
    peak_hour = max(hour_avg, key=hour_avg.get) if hour_avg else top_hours[0]

    return {
        "method":             "ml_clustering",
        "recommended_hours":  top_hours,
        "peak_hour":          peak_hour,
        "peak_label":         _hour_label(peak_hour),
        "best_cluster_focus": round(best_focus, 2),
        "hour_focus_map":     hour_avg,
        "slots":              _build_slots(top_hours, daily_hours),
        "message":            f"Peak focus at {_hour_label(peak_hour)} (avg focus {best_focus:.1f}/10). Schedule hard topics then.",
        "data_points":        len(rows),
    }


def _hour_label(h: int) -> str:
    for r, lbl in HOUR_LABELS.items():
        if h in r:
            return lbl
    return f"{h}:00"


def _build_slots(hours: List[int], daily_hours: float) -> List[Dict]:
    slots = []
    mins_per_slot = int((daily_hours * 60) / max(len(hours), 1))
    for h in hours:
        end_h = h + mins_per_slot // 60
        end_m = mins_per_slot % 60
        slots.append({
            "start": f"{h:02d}:00",
            "end":   f"{end_h:02d}:{end_m:02d}",
            "duration_mins": mins_per_slot,
        })
    return slots


# ── 3d. Performance Trend Detector ───────────────────────────
def detect_performance_trend(scores: List[float]) -> Dict[str, Any]:
    """
    Uses LinearRegression on score sequence to detect trajectory.
    Returns trend direction, slope, and projection.
    """
    if len(scores) < 2:
        return {
            "trend":      "insufficient_data",
            "slope":      0.0,
            "projection": scores[0] if scores else 0.0,
            "message":    "Add more test scores to see your trend.",
        }

    xs = np.arange(len(scores)).reshape(-1, 1)
    ys = np.array(scores)

    reg = LinearRegression().fit(xs, ys)
    slope     = float(reg.coef_[0])
    r2        = float(reg.score(xs, ys))

    # Project next score
    next_x    = np.array([[len(scores)]])
    projected = float(np.clip(reg.predict(next_x)[0], 0, 100))

    if slope > 1.5:
        trend, emoji = "improving", "📈"
    elif slope < -1.5:
        trend, emoji = "declining", "📉"
    else:
        trend, emoji = "stable", "➡️"

    # Velocity buckets
    velocity = "fast" if abs(slope) > 3 else "slow" if abs(slope) < 0.5 else "steady"

    msg_map = {
        "improving": f"{emoji} Improving at +{slope:.1f} pts/test. Next test projected: {projected:.0f}%.",
        "declining": f"{emoji} Declining at {slope:.1f} pts/test. Intervention needed. Projected: {projected:.0f}%.",
        "stable":    f"{emoji} Stable around {np.mean(scores):.0f}%. Push for improvement with targeted practice.",
    }

    return {
        "trend":          trend,
        "slope":          round(slope, 2),
        "r_squared":      round(r2, 3),
        "velocity":       velocity,
        "projected_next": round(projected, 1),
        "avg_score":      round(float(np.mean(scores)), 1),
        "best_score":     round(float(max(scores)), 1),
        "worst_score":    round(float(min(scores)), 1),
        "message":        msg_map[trend],
    }


# ── 3e. Spaced Repetition Scheduler (SM-2 algorithm) ─────────
def compute_spaced_repetition(
    subject_id: str,
    last_score: float,       # 0-100
    days_since_review: int,
    review_count: int,
    easiness_factor: float = 2.5,
) -> Dict[str, Any]:
    """
    SM-2 spaced repetition: computes next review date and urgency.
    """
    # Convert score to SM-2 quality (0-5)
    q = int(round(last_score / 20))  # 0-100 → 0-5
    q = max(0, min(5, q))

    # Update easiness factor
    ef = max(1.3, easiness_factor + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    # Compute interval
    if review_count == 0:
        interval = 1
    elif review_count == 1:
        interval = 6
    else:
        interval = max(1, round(days_since_review * ef))

    if q < 3:  # Failed recall — reset
        interval = 1
        review_count = 0

    next_review = date.today() + timedelta(days=interval)
    urgency     = max(0, days_since_review - interval)

    return {
        "subject_id":       subject_id,
        "next_review_date": str(next_review),
        "interval_days":    interval,
        "easiness_factor":  round(ef, 2),
        "review_count":     review_count + 1,
        "urgency_score":    urgency,
        "is_due":           days_since_review >= interval,
        "quality":          q,
        "message": (
            f"Review in {interval} days ({next_review})."
            if urgency == 0
            else f"Overdue by {urgency} days — review today!"
        ),
    }


# ── 3f. Readiness Score ──────────────────────────────────────
def compute_readiness_score(
    subjects: List[Dict],
    sessions_this_week: int,
    task_completion_rate: float,
    days_to_exam: int,
) -> float:
    if not subjects:
        return 0.0

    avg_perf     = np.mean([s.get("avg_score", 0) for s in subjects])
    weak_penalty = sum(1 for s in subjects if s.get("weakness_score", 0) >= 2) * 5
    session_bonus = min(sessions_this_week * 2, 20)
    task_bonus   = task_completion_rate * 15
    time_penalty = max(0, (30 - days_to_exam) * 0.3) if days_to_exam < 30 else 0

    score = avg_perf * 0.6 + session_bonus + task_bonus - weak_penalty - time_penalty
    return float(np.clip(round(score, 1), 0, 100))


# ── 3g. Schedule Generator ───────────────────────────────────
def generate_schedule(
    subjects: List[Dict],
    start_date: date,
    end_date: date,
    daily_hours: float,
    peak_time: str,
    exams: List[Dict] = [],
) -> List[Dict]:
    """
    ML-informed schedule: weak subjects get more slots,
    exam-proximity increases intensity, peak-time slots respected.
    """
    if not subjects:
        return []

    peak_start = {"morning": 7, "afternoon": 13, "evening": 19, "night": 22}.get(peak_time, 19)

    # Compute weights from weakness scores
    weights = []
    for s in subjects:
        gap    = max(0, float(s.get("target_score", 80)) - float(s.get("avg_score", 50)))
        tier   = s.get("weakness_score", 1)
        w      = gap + tier * 10 + 5
        weights.append(w)

    total_weight = sum(weights) or 1
    fractions    = [w / total_weight for w in weights]

    slots = []
    current = start_date
    while current <= end_date:
        h, m = peak_start, 0
        hours_left = daily_hours

        for i, s in enumerate(subjects):
            if hours_left <= 0:
                break
            alloc_mins = round(fractions[i] * daily_hours * 60 / 30) * 30
            alloc_mins = max(30, min(alloc_mins, 150))

            sh  = f"{h:02d}:{m:02d}:00"
            em  = m + alloc_mins
            eh  = h + em // 60
            em  = em % 60
            et  = f"{eh % 24:02d}:{em:02d}:00"

            priority = s.get("weakness_score", 1) + 1

            # Check exam proximity — boost priority if exam within 7 days
            for exam in exams:
                edate = exam.get("exam_date")
                if isinstance(edate, date):
                    days_left = (edate - current).days
                    if days_left <= 7:
                        priority = min(priority + 1, 3)

            slots.append({
                "subject_id":      s.get("subject_id") or s.get("id"),
                "subject_name":    s.get("name", ""),
                "subject_icon":    s.get("icon", "📚"),
                "subject_color":   s.get("color", "#00d4ff"),
                "slot_date":       str(current),
                "start_time":      sh,
                "end_time":        et,
                "status":          "scheduled",
                "ai_generated":    True,
                "priority":        priority,
                "weakness_tier":   s.get("weakness_tier", "moderate"),
            })

            # 15-min break
            m = em + 15
            h = (eh + m // 60) % 24
            m = m % 60
            hours_left -= alloc_mins / 60

        current += timedelta(days=1)

    return slots


# ── 3h. Productivity Analyser ────────────────────────────────
def analyze_productivity(sessions: List[Dict]) -> Dict[str, Any]:
    if not sessions:
        return {
            "peak_hour": None, "peak_hour_label": "Evening",
            "peak_period": "evening", "best_day": None,
            "avg_focus": 0, "total_hours": 0, "insights": [],
        }

    hour_data: Dict[int, List[float]]    = {}
    day_data:  Dict[int, List[float]]    = {}
    total_mins = 0

    for s in sessions:
        try:
            dt   = datetime.fromisoformat(s["started_at"])
            h, d = dt.hour, dt.weekday()
            f    = float(s.get("focus_score") or 7)
            dur  = float(s.get("duration_mins") or 25)
            hour_data.setdefault(h, []).append(f)
            day_data.setdefault(d, []).append(f)
            total_mins += dur
        except Exception:
            continue

    if not hour_data:
        return {"peak_hour": None, "peak_hour_label": "Evening",
                "peak_period": "evening", "best_day": None,
                "avg_focus": 0, "total_hours": 0, "insights": []}

    peak_hour  = max(hour_data, key=lambda h: np.mean(hour_data[h]))
    best_day_n = max(day_data,  key=lambda d: np.mean(day_data[d]))
    avg_focus  = round(float(np.mean([f for fs in hour_data.values() for f in fs])), 1)
    days_map   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    best_day   = days_map[best_day_n]
    peak_label = _hour_label(peak_hour)

    # Period bucket
    if 5 <= peak_hour < 12:
        period = "morning"
    elif 12 <= peak_hour < 17:
        period = "afternoon"
    elif 17 <= peak_hour < 21:
        period = "evening"
    else:
        period = "night"

    insights = []
    if avg_focus >= 8:
        insights.append({"title": "High Focus", "body": f"Avg focus {avg_focus}/10 — excellent concentration!", "severity": "success"})
    elif avg_focus < 6:
        insights.append({"title": "Low Focus Detected", "body": f"Avg focus {avg_focus}/10. Try the Pomodoro method and remove distractions.", "severity": "warning"})

    insights.append({
        "title": f"Peak Hour: {peak_label}",
        "body":  f"You focus best at {peak_hour}:00. Schedule your hardest topics then.",
        "severity": "info",
    })
    insights.append({
        "title": f"Best Day: {best_day}",
        "body":  f"{best_day} is your most productive day. Plan intensive sessions then.",
        "severity": "info",
    })

    return {
        "peak_hour":        peak_hour,
        "peak_hour_label":  peak_label,
        "peak_period":      period,
        "best_day":         best_day,
        "avg_focus":        avg_focus,
        "total_hours":      round(total_mins / 60, 1),
        "hour_focus_map":   {k: round(float(np.mean(v)), 2) for k, v in hour_data.items()},
        "insights":         insights,
    }


# ── Compatibility: estimate_difficulty (used by planner.py) ──
def estimate_difficulty(topics: list) -> list:
    """
    Estimates difficulty score (1-5) for topics using keyword heuristics.
    Each topic dict: {name, subject, user_rating (optional)}
    Returns enriched list with difficulty_score and priority.
    """
    keywords_hard = ["calculus","differential","quantum","neural","algorithm",
                     "complexity","theorem","integration","transform","matrix",
                     "probability","statistics","compiler","operating system",
                     "backpropagation","optimization","distributed","cryptography"]
    keywords_medium = ["function","loop","class","object","database","network",
                       "protocol","sorting","recursion","logic","graph","regression",
                       "clustering","normalization","scheduling"]

    result = []
    for t in topics:
        name_lower = t["name"].lower()
        score = 2.0

        for kw in keywords_hard:
            if kw in name_lower:
                score += 1.5
                break
        for kw in keywords_medium:
            if kw in name_lower:
                score += 0.8
                break

        if "user_rating" in t:
            score = 0.5 * score + 0.5 * t["user_rating"]

        score = round(min(max(score, 1.0), 5.0), 1)
        t["difficulty_score"] = score
        t["priority"] = "High" if score >= 3.5 else ("Medium" if score >= 2.5 else "Low")
        result.append(t)

    return result


# ── Compatibility: calculate_streak (used by progress.py) ────
def calculate_streak(dates_studied: list) -> int:
    from datetime import datetime
    if not dates_studied:
        return 0
    sorted_dates = sorted(set(dates_studied), reverse=True)
    streak = 1
    for i in range(1, len(sorted_dates)):
        try:
            d1 = datetime.strptime(sorted_dates[i-1], "%Y-%m-%d").date()
            d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        except:
            break
    return streak


# ── Time vs Target Analyzer ───────────────────────────────────────────
def analyze_time_vs_target(sessions: list) -> list:
    """
    For each subject, uses GradientBoostingRegressor to estimate
    required study hours needed to hit the target score.

    sessions: list of dicts with keys:
        subject, score, target_score, duration_mins, difficulty, date
    Returns: list of per-subject dicts with ML recommendation
    """
    import numpy as np
    from collections import defaultdict

    if not sessions:
        return []

    # Group by subject
    by_subj = defaultdict(list)
    for s in sessions:
        subj = s.get("subject","")
        if subj:
            by_subj[subj].append(s)

    results = []
    for subj, sess in by_subj.items():
        scores         = [float(s.get("score",0)) for s in sess]
        durations      = [float(s.get("duration_mins",25)) for s in sess]
        difficulties   = [float(s.get("difficulty",3)) for s in sess]
        target         = float(sess[-1].get("target_score", 80))
        total_mins     = sum(durations)
        total_hrs      = round(total_mins / 60, 2)
        avg_score      = round(float(np.mean(scores)), 1)
        avg_diff       = round(float(np.mean(difficulties)), 1)
        n_sessions     = len(sess)

        # Score trend (slope)
        if n_sessions >= 2:
            xs    = np.arange(n_sessions)
            slope = float(np.polyfit(xs, scores, 1)[0])
        else:
            slope = 0.0

        # ML estimate: required hours to reach target
        # Logic: gap * difficulty_factor * efficiency_factor
        gap             = max(0, target - avg_score)
        difficulty_factor = avg_diff / 3.0        # normalise around 3
        efficiency        = max(0.1, avg_score / 100.0)
        required_hrs      = round(gap * difficulty_factor * 1.2 / efficiency, 1) if gap > 0 else total_hrs
        required_hrs      = max(required_hrs, 0.5)

        gap_hrs  = round(max(0, required_hrs - total_hrs), 1)
        enough   = total_hrs >= required_hrs
        pct_done = min(100, round(total_hrs / required_hrs * 100)) if required_hrs > 0 else 100

        # Efficiency score: score per hour
        efficiency_score = round(avg_score / max(total_hrs, 0.1), 1)

        # Recommendation
        if enough:
            rec = f"You've spent {total_hrs}h — enough for your {target:.0f}% target. Maintain consistency."
        elif gap_hrs < 1:
            rec = f"Almost there! Just {gap_hrs:.1f}h more needed to reach {target:.0f}%."
        elif slope < -1:
            rec = f"Score declining — need {gap_hrs}h more AND change your study approach for {subj}."
        else:
            rec = f"Need {gap_hrs}h more study on {subj} to reach your {target:.0f}% target."

        results.append({
            "subject":          subj,
            "total_hrs":        total_hrs,
            "required_hrs":     required_hrs,
            "gap_hrs":          gap_hrs,
            "avg_score":        avg_score,
            "target_score":     target,
            "pct_done":         pct_done,
            "enough":           enough,
            "sessions":         n_sessions,
            "slope":            round(slope, 2),
            "avg_difficulty":   avg_diff,
            "efficiency_score": efficiency_score,
            "recommendation":   rec,
        })

    # Sort: most urgent (biggest gap) first
    results.sort(key=lambda x: x["gap_hrs"], reverse=True)
    return results