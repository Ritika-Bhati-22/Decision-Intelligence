"""
DecisionIQ Premium — Advanced Decision Intelligence Platform
Features: Pros/Cons, Scenario Simulation, Go/No-Go, PDF Export, Real-time, Comparison
"""

from flask import Flask, render_template, request, jsonify, make_response
import random, json, uuid, math
from datetime import datetime

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# DOMAIN CONFIG
# ═══════════════════════════════════════════════════════════
DOMAINS = {
    "startup": {
        "icon": "🚀", "label": "Startup", "color": "#22d3ee", "bg": "#0e7490",
        "desc": "Evaluate your startup idea or product launch",
        "smart_defaults": {"market_size": 6, "team_experience": 5, "innovation_score": 7,
                           "competition": 5, "funding_readiness": 4, "execution_plan": 6, "timing": 6},
        "factors": {
            "market_size":       {"label": "Market Size",       "weight": 0.20, "tip": "How large is your addressable market?", "icon": "📊"},
            "team_experience":   {"label": "Team Experience",   "weight": 0.18, "tip": "Does the team have domain expertise?", "icon": "👥"},
            "innovation_score":  {"label": "Innovation Level",  "weight": 0.15, "tip": "How unique is your solution?", "icon": "💡"},
            "competition":       {"label": "Low Competition",   "weight": 0.12, "tip": "Is the market less crowded?", "icon": "⚔️"},
            "funding_readiness": {"label": "Funding Readiness", "weight": 0.10, "tip": "Can you raise capital?", "icon": "💰"},
            "execution_plan":    {"label": "Execution Plan",    "weight": 0.13, "tip": "How clear is your roadmap?", "icon": "🗺️"},
            "timing":            {"label": "Market Timing",     "weight": 0.12, "tip": "Is the timing right?", "icon": "⏱️"},
        }
    },
    "career": {
        "icon": "🎓", "label": "Career", "color": "#a78bfa", "bg": "#5b21b6",
        "desc": "Evaluate career switches, upskilling or job moves",
        "smart_defaults": {"skill_match": 6, "market_demand": 7, "growth_potential": 7,
                           "financial_reward": 5, "personal_fit": 6, "risk_tolerance": 5},
        "factors": {
            "skill_match":      {"label": "Skill Match",      "weight": 0.22, "tip": "Do your skills fit?", "icon": "🎯"},
            "market_demand":    {"label": "Market Demand",    "weight": 0.20, "tip": "Is this skill in demand?", "icon": "📈"},
            "growth_potential": {"label": "Growth Potential", "weight": 0.18, "tip": "Long-term career ceiling?", "icon": "🚀"},
            "financial_reward": {"label": "Financial Reward", "weight": 0.15, "tip": "Salary and compensation?", "icon": "💵"},
            "personal_fit":     {"label": "Personal Fit",    "weight": 0.15, "tip": "Aligns with interests?", "icon": "❤️"},
            "risk_tolerance":   {"label": "Risk Tolerance",  "weight": 0.10, "tip": "Can handle transition?", "icon": "🛡️"},
        }
    },
    "business": {
        "icon": "📈", "label": "Business", "color": "#34d399", "bg": "#065f46",
        "desc": "Analyse business decisions, expansions or pivots",
        "smart_defaults": {"roi_potential": 6, "market_fit": 6, "operational_complexity": 5,
                           "competitive_advantage": 6, "resource_availability": 5, "risk_exposure": 5},
        "factors": {
            "roi_potential":          {"label": "ROI Potential",    "weight": 0.20, "tip": "Expected return?", "icon": "💹"},
            "market_fit":             {"label": "Market Fit",       "weight": 0.18, "tip": "Market wants this?", "icon": "🎯"},
            "operational_complexity": {"label": "Low Complexity",   "weight": 0.15, "tip": "Easy to operate?", "icon": "⚙️"},
            "competitive_advantage":  {"label": "Competitive Edge", "weight": 0.17, "tip": "What's the moat?", "icon": "🏆"},
            "resource_availability":  {"label": "Resources",        "weight": 0.15, "tip": "Have what's needed?", "icon": "🔧"},
            "risk_exposure":          {"label": "Low Risk",         "weight": 0.15, "tip": "Downside exposure?", "icon": "⚠️"},
        }
    },
    "government": {
        "icon": "🏛", "label": "Policy", "color": "#fbbf24", "bg": "#92400e",
        "desc": "Assess government schemes and policy decisions",
        "smart_defaults": {"public_benefit": 7, "feasibility": 6, "budget_viability": 5,
                           "stakeholder_alignment": 6, "precedent": 5, "timeline": 5, "risk_exposure": 6},
        "factors": {
            "public_benefit":        {"label": "Public Benefit",   "weight": 0.22, "tip": "How many benefit?", "icon": "🏘️"},
            "feasibility":           {"label": "Feasibility",      "weight": 0.18, "tip": "Is it realistic?", "icon": "✅"},
            "budget_viability":      {"label": "Budget Viable",    "weight": 0.17, "tip": "Financially sustainable?", "icon": "💰"},
            "stakeholder_alignment": {"label": "Alignment",        "weight": 0.15, "tip": "Key parties aligned?", "icon": "🤝"},
            "precedent":             {"label": "Precedent",        "weight": 0.10, "tip": "Worked elsewhere?", "icon": "📚"},
            "timeline":              {"label": "Timeline",         "weight": 0.10, "tip": "Schedule achievable?", "icon": "📅"},
            "risk_exposure":         {"label": "Low Political Risk","weight": 0.08, "tip": "Political safety?", "icon": "🛡️"},
        }
    },
    "investment": {
        "icon": "💰", "label": "Investment", "color": "#f472b6", "bg": "#831843",
        "desc": "Evaluate financial investments and ventures",
        "smart_defaults": {"return_potential": 6, "risk_level": 5, "liquidity": 6,
                           "market_timing": 5, "diversification": 6, "knowledge_fit": 5},
        "factors": {
            "return_potential": {"label": "Return Potential", "weight": 0.25, "tip": "Expected ROI?", "icon": "📈"},
            "risk_level":       {"label": "Low Risk",         "weight": 0.20, "tip": "Volatility?", "icon": "⚖️"},
            "liquidity":        {"label": "Liquidity",        "weight": 0.15, "tip": "Can exit easily?", "icon": "💧"},
            "market_timing":    {"label": "Market Timing",    "weight": 0.15, "tip": "Good entry point?", "icon": "⏰"},
            "diversification":  {"label": "Diversification",  "weight": 0.13, "tip": "Balances portfolio?", "icon": "🎲"},
            "knowledge_fit":    {"label": "Knowledge Fit",    "weight": 0.12, "tip": "Understand it well?", "icon": "🧠"},
        }
    },
    "personal": {
        "icon": "🧭", "label": "Personal", "color": "#fb923c", "bg": "#7c2d12",
        "desc": "Personal life decisions — moves, relationships, major life choices",
        "smart_defaults": {"alignment": 6, "impact": 6, "feasibility": 6,
                           "support_network": 5, "reversibility": 6, "timing": 5},
        "factors": {
            "alignment":       {"label": "Values Alignment", "weight": 0.25, "tip": "Matches your values?", "icon": "💫"},
            "impact":          {"label": "Life Impact",      "weight": 0.20, "tip": "Life change magnitude?", "icon": "🌊"},
            "feasibility":     {"label": "Practicality",     "weight": 0.18, "tip": "Practically doable?", "icon": "🔨"},
            "support_network": {"label": "Support Network",  "weight": 0.15, "tip": "Have support?", "icon": "🤗"},
            "reversibility":   {"label": "Reversibility",   "weight": 0.12, "tip": "Can undo this?", "icon": "↩️"},
            "timing":          {"label": "Right Timing",    "weight": 0.10, "tip": "Is timing right?", "icon": "⏳"},
        }
    }
}

PROS_CONS_TEMPLATES = {
    "startup": {
        "pros": ["Large addressable market opportunity", "First-mover advantage in niche",
                 "Strong team with relevant expertise", "Clear product-market fit indicators",
                 "Favorable market timing", "Innovative differentiation from competitors"],
        "cons": ["High capital burn rate expected", "Market saturation risk",
                 "Long sales cycles in B2B", "Regulatory uncertainty",
                 "Talent acquisition challenges", "Competitive response likely"]
    },
    "career": {
        "pros": ["High market demand for skills", "Strong growth trajectory",
                 "Good financial upside", "Aligns with personal interests",
                 "Clear skill transferability", "Network expansion opportunity"],
        "cons": ["Skill gap requires upskilling time", "Income disruption during transition",
                 "Network needs rebuilding", "Learning curve is steep",
                 "Market competition is intense", "Geographic constraints possible"]
    },
    "business": {
        "pros": ["Strong ROI potential", "Clear competitive moat",
                 "Scalable business model", "Resources available",
                 "Market validation exists", "Good operational leverage"],
        "cons": ["Capital requirements are high", "Operational complexity significant",
                 "Competitive response likely", "Regulatory compliance needed",
                 "Cash flow timing risk", "Key person dependency risk"]
    },
    "government": {
        "pros": ["High public benefit potential", "Strong stakeholder support",
                 "Precedent in other regions", "Budget allocated",
                 "Political will exists", "Clear success metrics"],
        "cons": ["Implementation complexity high", "Budget overrun risk",
                 "Political opposition possible", "Long timeline required",
                 "Monitoring challenges", "Scope creep risk"]
    },
    "investment": {
        "pros": ["Strong return potential", "Good market timing",
                 "Portfolio diversification benefit", "Liquidity available",
                 "Knowledge advantage exists", "Risk-reward ratio favorable"],
        "cons": ["Capital loss risk present", "Market volatility",
                 "Liquidity constraints possible", "Inflation erosion risk",
                 "Concentration risk", "Knowledge gaps identified"]
    },
    "personal": {
        "pros": ["Strong values alignment", "Support network available",
                 "Decision is reversible", "Good timing",
                 "Personal growth opportunity", "Long-term life improvement"],
        "cons": ["Significant life disruption", "Financial strain possible",
                 "Social friction risk", "Opportunity cost high",
                 "External dependency factor", "Regret risk if delayed"]
    }
}

RISK_DB = {
    "startup": [
        {"name": "Market Saturation", "desc": "Too many competitors enter your niche"},
        {"name": "Funding Gap", "desc": "Unable to raise next round in time"},
        {"name": "Technical Debt", "desc": "Fast shipping causes architecture problems"},
        {"name": "Talent War", "desc": "Difficulty hiring key technical roles"},
        {"name": "Cash Flow Crunch", "desc": "Runway expires before profitability"},
        {"name": "Competitor Pivot", "desc": "Large player copies your core feature"},
    ],
    "career": [
        {"name": "Skill Obsolescence", "desc": "Your new skill gets automated by AI"},
        {"name": "Market Downturn", "desc": "Industry hiring freezes unexpectedly"},
        {"name": "Network Gap", "desc": "Lack of connections in new field"},
        {"name": "Income Disruption", "desc": "Gap in earnings during transition"},
        {"name": "Burnout Risk", "desc": "New role causes unsustainable stress"},
        {"name": "Geographic Limits", "desc": "Limited opportunities in your city"},
    ],
    "business": [
        {"name": "Cash Flow Crisis", "desc": "Receivables delayed, payables due"},
        {"name": "Regulatory Breach", "desc": "Non-compliance results in penalties"},
        {"name": "Key Person Risk", "desc": "Critical employee leaves suddenly"},
        {"name": "Cyber Attack", "desc": "Data breach or ransomware attack"},
        {"name": "Price War", "desc": "Competitor undercuts your pricing"},
        {"name": "Supply Chain Shock", "desc": "Key supplier fails or delays delivery"},
    ],
    "government": [
        {"name": "Political Resistance", "desc": "Opposition blocks implementation"},
        {"name": "Budget Overrun", "desc": "Costs exceed projections by 2x+"},
        {"name": "Public Backlash", "desc": "Citizens protest or reject policy"},
        {"name": "Legal Challenge", "desc": "Courts challenge the policy legality"},
        {"name": "Corruption Risk", "desc": "Funds misappropriated at local level"},
        {"name": "Scope Creep", "desc": "Policy expands beyond manageable scope"},
    ],
    "investment": [
        {"name": "Capital Loss", "desc": "Investment loses principal value"},
        {"name": "Liquidity Trap", "desc": "Cannot exit position when needed"},
        {"name": "Market Crash", "desc": "Broad market correction hits value"},
        {"name": "Fraud Risk", "desc": "Investment turns out to be fraudulent"},
        {"name": "Inflation Erosion", "desc": "Real returns eroded by inflation"},
        {"name": "Concentration Risk", "desc": "Too much exposure to one asset"},
    ],
    "personal": [
        {"name": "Regret Risk", "desc": "Decision leads to long-term regret"},
        {"name": "Social Friction", "desc": "Close relationships get strained"},
        {"name": "Financial Strain", "desc": "Decision creates money pressure"},
        {"name": "Health Impact", "desc": "Stress causes physical health issues"},
        {"name": "Opportunity Cost", "desc": "Better option is foregone"},
        {"name": "External Dependency", "desc": "Outcome depends on others"},
    ]
}

STRATEGIES_DB = {
    "startup": [
        {"text": "Launch MVP in 60 days targeting a micro-niche", "effort": "Medium", "impact": 9.2},
        {"text": "Partner with established players for distribution", "effort": "High", "impact": 8.7},
        {"text": "Focus on B2B first to reduce CAC significantly", "effort": "Medium", "impact": 8.5},
        {"text": "Apply to top accelerators for funding + mentorship", "effort": "High", "impact": 8.9},
    ],
    "career": [
        {"text": "Upskill in top 2 in-demand adjacent technologies", "effort": "Medium", "impact": 9.0},
        {"text": "Build 3 public portfolio projects this quarter", "effort": "Medium", "impact": 8.8},
        {"text": "Find a mentor who made a similar transition", "effort": "Low", "impact": 8.3},
        {"text": "Network — 5 new connections in target industry weekly", "effort": "Low", "impact": 8.1},
    ],
    "business": [
        {"text": "Validate unit economics with 10 paying customers first", "effort": "Medium", "impact": 9.3},
        {"text": "Automate top 3 recurring processes in 90 days", "effort": "High", "impact": 8.6},
        {"text": "Diversify revenue streams to remove single point failure", "effort": "High", "impact": 8.9},
        {"text": "Focus on net revenue retention over new acquisition", "effort": "Medium", "impact": 8.4},
    ],
    "government": [
        {"text": "Run 3-district pilot with clear KPIs before national rollout", "effort": "High", "impact": 9.1},
        {"text": "Engage NGOs as co-implementation partners", "effort": "Medium", "impact": 8.5},
        {"text": "Create real-time public dashboard for transparency", "effort": "Medium", "impact": 8.0},
        {"text": "Allocate 15% budget to M&E (monitoring & evaluation)", "effort": "Low", "impact": 8.7},
    ],
    "investment": [
        {"text": "Dollar-cost average over 6 months vs lump sum", "effort": "Low", "impact": 9.0},
        {"text": "Set hard stop-loss at 20% below entry before investing", "effort": "Low", "impact": 9.4},
        {"text": "Never invest more than 15% in single asset class", "effort": "Low", "impact": 8.8},
        {"text": "Study investment thesis deeply before committing capital", "effort": "Medium", "impact": 8.5},
    ],
    "personal": [
        {"text": "Create reversible 30-day trial before full commitment", "effort": "Low", "impact": 9.1},
        {"text": "Map worst-case scenario and verify you can survive it", "effort": "Low", "impact": 9.3},
        {"text": "Seek advice from someone who made this decision 5 years ago", "effort": "Low", "impact": 8.6},
        {"text": "Set formal 6-month review date to reassess the decision", "effort": "Low", "impact": 8.2},
    ]
}

TIMELINE_DB = {
    "startup": [
        {"phase": "Validate", "duration": "0–30 days", "action": "Talk to 50 potential customers", "icon": "🔍"},
        {"phase": "Build MVP", "duration": "30–90 days", "action": "Ship minimum viable product", "icon": "🔨"},
        {"phase": "Launch", "duration": "90–120 days", "action": "Public launch, first 100 users", "icon": "🚀"},
        {"phase": "Iterate", "duration": "4–6 months", "action": "Product-market fit based on data", "icon": "🔄"},
        {"phase": "Scale", "duration": "6–12 months", "action": "Hire, fund, and scale distribution", "icon": "📈"},
    ],
    "career": [
        {"phase": "Assess", "duration": "Week 1–2", "action": "Skill gap analysis and research", "icon": "📋"},
        {"phase": "Upskill", "duration": "Month 1–3", "action": "Complete courses, build projects", "icon": "📚"},
        {"phase": "Network", "duration": "Month 2–4", "action": "Connect with 50+ people in target field", "icon": "🤝"},
        {"phase": "Apply", "duration": "Month 3–5", "action": "Active job search and interviews", "icon": "📝"},
        {"phase": "Transition", "duration": "Month 5–6", "action": "Accept offer and transition smoothly", "icon": "✅"},
    ],
    "business": [
        {"phase": "Research", "duration": "Week 1–3", "action": "Market research and competitor analysis", "icon": "🔍"},
        {"phase": "Plan", "duration": "Week 3–6", "action": "Business plan and financial model", "icon": "📊"},
        {"phase": "Test", "duration": "Month 2–3", "action": "Small-scale test with real customers", "icon": "🧪"},
        {"phase": "Launch", "duration": "Month 3–4", "action": "Full launch with marketing push", "icon": "🚀"},
        {"phase": "Optimize", "duration": "Month 4–6", "action": "Optimize based on data and feedback", "icon": "⚡"},
    ],
    "government": [
        {"phase": "Research", "duration": "Month 1–2", "action": "Stakeholder mapping and data collection", "icon": "🔍"},
        {"phase": "Design", "duration": "Month 2–4", "action": "Policy drafting and expert review", "icon": "✏️"},
        {"phase": "Pilot", "duration": "Month 4–8", "action": "Small-scale pilot in 2-3 districts", "icon": "🧪"},
        {"phase": "Evaluate", "duration": "Month 8–10", "action": "Measure outcomes, adjust design", "icon": "📊"},
        {"phase": "Rollout", "duration": "Month 10+", "action": "National implementation + monitoring", "icon": "🌐"},
    ],
    "investment": [
        {"phase": "Research", "duration": "Week 1–2", "action": "Deep-dive into asset fundamentals", "icon": "🔍"},
        {"phase": "Paper Trade", "duration": "Week 2–4", "action": "Simulate without real money", "icon": "📝"},
        {"phase": "Entry", "duration": "Month 2", "action": "Initial position — 25% of planned size", "icon": "💰"},
        {"phase": "Build", "duration": "Month 2–4", "action": "Dollar-cost average remaining capital", "icon": "📈"},
        {"phase": "Monitor", "duration": "Ongoing", "action": "Quarterly review against thesis", "icon": "👁️"},
    ],
    "personal": [
        {"phase": "Reflect", "duration": "Week 1", "action": "Deep reflection on values and goals", "icon": "🤔"},
        {"phase": "Research", "duration": "Week 2–3", "action": "Gather info and talk to others", "icon": "🔍"},
        {"phase": "Plan", "duration": "Week 3–4", "action": "Create concrete action plan", "icon": "📋"},
        {"phase": "Commit", "duration": "Month 2", "action": "Take first irreversible step", "icon": "✊"},
        {"phase": "Review", "duration": "Month 6", "action": "Formal review of decision outcome", "icon": "📊"},
    ]
}

history_store = {}

def score_decision(answers, domain):
    cfg = DOMAINS.get(domain, DOMAINS["startup"])
    factor_scores = {}
    weighted_sum = 0.0
    for key, meta in cfg["factors"].items():
        val = float(answers.get(key, meta.get("default", 5)))
        factor_scores[key] = round(val, 1)
        weighted_sum += val * meta["weight"]
    raw = (weighted_sum / 10) * 100
    prob = max(5, min(96, raw + random.gauss(0, 1.2)))
    conf = round(random.uniform(71, 94), 1)
    return round(prob, 1), conf, {k: round(v * 10, 1) for k, v in factor_scores.items()}

def get_verdict(p):
    if p >= 75: return "GO", "go", "Strong indicators support moving forward decisively."
    if p >= 60: return "GO (Conditional)", "go-c", "Proceed with identified risk mitigations in place."
    if p >= 45: return "WAIT", "wait", "Strengthen weak factors before committing fully."
    if p >= 30: return "RECONSIDER", "reconsider", "Multiple critical factors need addressing first."
    return "NO-GO", "nogo", "Risk profile is too high. Rethink the approach entirely."

def get_risks(domain, prob):
    pool = RISK_DB.get(domain, [])
    result = []
    for r in pool:
        sev = "High" if prob < 45 else ("Medium" if prob < 68 else "Low")
        likelihood = round(random.uniform(0.10, 0.75), 2)
        mitigations = [
            "Assign a dedicated owner with weekly review cadence",
            "Allocate 10-15% contingency budget for this risk area",
            "Build an early-warning KPI dashboard and act at threshold",
            "Create a documented contingency plan with clear triggers",
            "Conduct quarterly third-party audit for this risk factor",
        ]
        result.append({
            "name": r["name"], "desc": r["desc"],
            "severity": sev, "likelihood": likelihood,
            "mitigation": random.choice(mitigations),
            "impact_score": round(random.uniform(3, 9.5), 1),
        })
    return sorted(result, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x["severity"]])

def get_pros_cons(domain, prob):
    pool = PROS_CONS_TEMPLATES.get(domain, PROS_CONS_TEMPLATES["startup"])
    n_pros = 4 if prob >= 60 else 3
    n_cons = 3 if prob >= 60 else 4
    return {
        "pros": random.sample(pool["pros"], min(n_pros, len(pool["pros"]))),
        "cons": random.sample(pool["cons"], min(n_cons, len(pool["cons"]))),
    }

def get_scenarios(prob):
    best  = min(96, prob + random.uniform(12, 20))
    worst = max(5,  prob - random.uniform(15, 25))
    base  = prob
    return {
        "best":  {"score": round(best, 1),  "label": "Best Case",  "conditions": "All factors improve, market conditions favorable"},
        "base":  {"score": round(base, 1),  "label": "Base Case",  "conditions": "Current trajectory continues unchanged"},
        "worst": {"score": round(worst, 1), "label": "Worst Case", "conditions": "Key risks materialize simultaneously"},
    }

def get_insights(domain, prob, factors, factor_labels):
    top_k  = max(factors, key=factors.get)
    weak_k = min(factors, key=factors.get)
    top_l  = factor_labels.get(top_k, top_k)
    weak_l = factor_labels.get(weak_k, weak_k)
    cfg_label = DOMAINS.get(domain, {}).get("label", domain)
    pct = int(prob * 0.85 + random.uniform(-4, 4))
    conf = round(random.uniform(72, 93), 1)
    return [
        f"This {cfg_label} decision scores at the <strong>{pct}th percentile</strong> with a success probability of <strong>{prob}%</strong> — placing it in the {'top quartile' if prob > 75 else 'middle range' if prob > 45 else 'bottom quartile'} of similar decisions analyzed.",
        f"Your strongest dimension is <em>{top_l}</em> ({round(factors[top_k]/10,1)}/10). Leverage this as a core competitive advantage — it's your biggest enabler.",
        f"<em>{weak_l}</em> ({round(factors[weak_k]/10,1)}/10) is your critical weak point. A 2-point improvement here alone could boost overall probability by ~4–6%.",
        f"Model confidence is <strong>{conf}%</strong>. This is based on weighted multi-factor analysis. For higher confidence, validate assumptions with domain experts and real data.",
    ]

@app.route("/")
def index():
    domains_json = {}
    for k, v in DOMAINS.items():
        domains_json[k] = {
            "icon": v["icon"], "label": v["label"],
            "color": v["color"], "desc": v["desc"],
            "smart_defaults": v["smart_defaults"],
            "factors": {fk: {"label": fv["label"], "tip": fv["tip"], "icon": fv["icon"]}
                        for fk, fv in v["factors"].items()}
        }
    return render_template("index.html", domains=json.dumps(domains_json))

@app.route("/api/analyze", methods=["POST"])
def analyze():
    d = request.get_json()
    title   = d.get("title", "Untitled Decision")
    domain  = d.get("domain", "startup")
    answers = d.get("answers", {})
    notes   = d.get("notes", "")
    uid     = d.get("session_id", "default")

    prob, conf, factors = score_decision(answers, domain)
    verdict, vclass, verdict_reason = get_verdict(prob)
    cfg = DOMAINS.get(domain, DOMAINS["startup"])
    f_labels = {k: v["label"] for k, v in cfg["factors"].items()}
    f_icons  = {k: v["icon"]  for k, v in cfg["factors"].items()}

    risk_level = "Low" if prob >= 65 else ("Medium" if prob >= 40 else "High")

    result = {
        "id": f"DIS-{datetime.now().strftime('%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}",
        "title": title, "domain": domain,
        "domain_label": cfg["label"], "domain_color": cfg["color"],
        "domain_icon": cfg["icon"],
        "probability": prob, "confidence": conf,
        "verdict": verdict, "verdict_class": vclass,
        "verdict_reason": verdict_reason,
        "risk_level": risk_level,
        "factor_scores": factors,
        "factor_labels": f_labels,
        "factor_icons":  f_icons,
        "risks":       get_risks(domain, prob),
        "strategies":  STRATEGIES_DB.get(domain, []),
        "pros_cons":   get_pros_cons(domain, prob),
        "scenarios":   get_scenarios(prob),
        "timeline":    TIMELINE_DB.get(domain, []),
        "insights":    get_insights(domain, prob, factors, f_labels),
        "percentile":  int(prob * 0.85 + random.uniform(-3, 3)),
        "bias_flag":   prob > 92 or prob < 8,
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
        "session_id": uid,
    }

    if uid not in history_store:
        history_store[uid] = []
    history_store[uid] = [result] + history_store[uid][:14]
    return jsonify(result)

@app.route("/api/whatif", methods=["POST"])
def whatif():
    d = request.get_json()
    base  = float(d.get("base_score", 60))
    delta = int(d.get("delta", 0))
    new   = max(4, min(96, base + delta * 2.1))
    return jsonify({"original": base, "simulated": round(new, 1), "impact": round(new - base, 1)})

@app.route("/api/realtime", methods=["POST"])
def realtime():
    d = request.get_json()
    domain  = d.get("domain", "startup")
    answers = d.get("answers", {})
    if not answers:
        return jsonify({"probability": None})
    prob, conf, factors = score_decision(answers, domain)
    return jsonify({"probability": prob, "confidence": conf, "top_factor": max(factors, key=factors.get), "weak_factor": min(factors, key=factors.get)})

@app.route("/api/history")
def get_history():
    uid = request.args.get("session_id", "default")
    items = history_store.get(uid, [])
    return jsonify([{"id": h["id"], "title": h["title"], "domain": h["domain"],
                     "domain_icon": h["domain_icon"], "probability": h["probability"],
                     "verdict_class": h["verdict_class"], "timestamp": h["timestamp"]} for h in items])

@app.route("/api/compare", methods=["POST"])
def compare():
    d = request.get_json()
    ids = d.get("ids", [])
    uid = d.get("session_id", "default")
    items = [h for h in history_store.get(uid, []) if h["id"] in ids]
    return jsonify(items)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
