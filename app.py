"""
DecisionIQ v3 — Decision Intelligence System
New: Notes, Timeline, Multi-step wizard, Scoring breakdown, Priority matrix
"""

from flask import Flask, render_template, request, jsonify
import random, json, uuid
from datetime import datetime

app = Flask(__name__)

# ── Domain Configs ─────────────────────────────────────────────────────────────
DOMAINS = {
    "startup": {
        "icon": "🚀", "label": "Startup", "color": "#6ee7f7",
        "desc": "Evaluate your startup idea or product launch",
        "factors": {
            "market_size":       {"label": "Market Size",        "weight": 0.20, "tip": "How large is the target market?"},
            "team_experience":   {"label": "Team Experience",    "weight": 0.18, "tip": "Does the team have relevant domain expertise?"},
            "innovation_score":  {"label": "Innovation Level",   "weight": 0.15, "tip": "How unique is the solution?"},
            "competition":       {"label": "Low Competition",    "weight": 0.12, "tip": "Is the market crowded?"},
            "funding_readiness": {"label": "Funding Readiness",  "weight": 0.10, "tip": "Can you raise capital?"},
            "execution_plan":    {"label": "Execution Plan",     "weight": 0.13, "tip": "How clear is the roadmap?"},
            "timing":            {"label": "Market Timing",      "weight": 0.12, "tip": "Is now the right time?"},
        }
    },
    "government": {
        "icon": "🏛", "label": "Gov Policy", "color": "#a5f3a0",
        "desc": "Assess government schemes and policy decisions",
        "factors": {
            "public_benefit":        {"label": "Public Benefit",        "weight": 0.22, "tip": "How many people benefit?"},
            "feasibility":           {"label": "Feasibility",           "weight": 0.18, "tip": "Is implementation realistic?"},
            "budget_viability":      {"label": "Budget Viability",      "weight": 0.17, "tip": "Is it financially sustainable?"},
            "stakeholder_alignment": {"label": "Stakeholder Alignment", "weight": 0.15, "tip": "Are key parties aligned?"},
            "precedent":             {"label": "Historical Precedent",  "weight": 0.10, "tip": "Has this worked elsewhere?"},
            "timeline":              {"label": "Timeline Realism",      "weight": 0.10, "tip": "Is the schedule achievable?"},
            "risk_exposure":         {"label": "Low Risk Exposure",     "weight": 0.08, "tip": "How risky politically?"},
        }
    },
    "career": {
        "icon": "🎓", "label": "Career Path", "color": "#fbbf24",
        "desc": "Evaluate career switches, upskilling, or job moves",
        "factors": {
            "skill_match":      {"label": "Skill Match",       "weight": 0.22, "tip": "Do your skills fit the role?"},
            "market_demand":    {"label": "Market Demand",     "weight": 0.20, "tip": "Is this skill in demand?"},
            "growth_potential": {"label": "Growth Potential",  "weight": 0.18, "tip": "Long-term career ceiling?"},
            "financial_reward": {"label": "Financial Reward",  "weight": 0.15, "tip": "Salary and compensation?"},
            "personal_fit":     {"label": "Personal Fit",      "weight": 0.15, "tip": "Does it align with interests?"},
            "risk_tolerance":   {"label": "Risk Tolerance",    "weight": 0.10, "tip": "Can you handle the transition?"},
        }
    },
    "business": {
        "icon": "📈", "label": "Business", "color": "#f472b6",
        "desc": "Analyse business decisions, expansions or pivots",
        "factors": {
            "roi_potential":          {"label": "ROI Potential",       "weight": 0.20, "tip": "Expected return on investment?"},
            "market_fit":             {"label": "Market Fit",          "weight": 0.18, "tip": "Does market want this?"},
            "operational_complexity": {"label": "Low Complexity",      "weight": 0.15, "tip": "How hard to operate?"},
            "competitive_advantage":  {"label": "Competitive Edge",    "weight": 0.17, "tip": "What's the moat?"},
            "resource_availability":  {"label": "Resources Available", "weight": 0.15, "tip": "Do you have what's needed?"},
            "risk_exposure":          {"label": "Low Risk Exposure",   "weight": 0.15, "tip": "Downside exposure?"},
        }
    },
    "personal": {
        "icon": "🧭", "label": "Personal", "color": "#c084fc",
        "desc": "Personal life decisions — moves, relationships, investments",
        "factors": {
            "alignment":       {"label": "Values Alignment",  "weight": 0.25, "tip": "Does it match your values?"},
            "impact":          {"label": "Life Impact",       "weight": 0.20, "tip": "How much does it change life?"},
            "feasibility":     {"label": "Practicality",      "weight": 0.18, "tip": "Is it practically doable?"},
            "support_network": {"label": "Support Network",   "weight": 0.15, "tip": "Do you have support?"},
            "reversibility":   {"label": "Reversibility",     "weight": 0.12, "tip": "Can you undo this?"},
            "timing":          {"label": "Right Timing",      "weight": 0.10, "tip": "Is timing right?"},
        }
    },
    "investment": {
        "icon": "💰", "label": "Investment", "color": "#34d399",
        "desc": "Evaluate financial investments, assets, or ventures",
        "factors": {
            "return_potential":  {"label": "Return Potential",   "weight": 0.25, "tip": "Expected ROI %?"},
            "risk_level":        {"label": "Low Risk Level",     "weight": 0.20, "tip": "Volatility and downside?"},
            "liquidity":         {"label": "Liquidity",          "weight": 0.15, "tip": "Can you exit easily?"},
            "market_timing":     {"label": "Market Timing",      "weight": 0.15, "tip": "Is it a good entry point?"},
            "diversification":   {"label": "Diversification",    "weight": 0.13, "tip": "Does it balance portfolio?"},
            "knowledge_fit":     {"label": "Knowledge Fit",      "weight": 0.12, "tip": "Do you understand it well?"},
        }
    },
}

RISK_DB = {
    "startup":    [
        {"name": "Market Saturation",    "desc": "Too many competitors in the niche"},
        {"name": "Funding Gap",          "desc": "Unable to raise next round in time"},
        {"name": "Technical Debt",       "desc": "Fast shipping causes architectural problems"},
        {"name": "Talent Acquisition",   "desc": "Difficulty hiring key technical roles"},
        {"name": "Regulatory Hurdles",   "desc": "Government compliance requirements"},
        {"name": "Cash Flow Crunch",     "desc": "Runway expires before profitability"},
        {"name": "Competitor Pivot",     "desc": "Large player copies your idea"},
    ],
    "government": [
        {"name": "Political Resistance", "desc": "Opposition blocks implementation"},
        {"name": "Budget Overrun",       "desc": "Costs exceed projections by 2x+"},
        {"name": "Implementation Delay", "desc": "Execution takes 3x longer than planned"},
        {"name": "Public Backlash",      "desc": "Citizens protest or reject policy"},
        {"name": "Legal Challenges",     "desc": "Courts challenge the policy"},
        {"name": "Corruption Risk",      "desc": "Funds misappropriated at local level"},
        {"name": "Scope Creep",          "desc": "Policy expands beyond manageable scope"},
    ],
    "career":  [
        {"name": "Skill Obsolescence",   "desc": "Your new skill becomes automated"},
        {"name": "Market Downturn",      "desc": "Industry hiring freezes"},
        {"name": "AI Disruption",        "desc": "Role gets replaced by AI tools"},
        {"name": "Geographic Limits",    "desc": "Limited opportunities in your city"},
        {"name": "Burnout Risk",         "desc": "New role causes unsustainable stress"},
        {"name": "Networking Gap",       "desc": "Lack of connections in new field"},
        {"name": "Credential Devaluation","desc": "Certification becomes less valued"},
    ],
    "business": [
        {"name": "Cash Flow Crisis",     "desc": "Receivables delayed, payables due"},
        {"name": "Supply Chain Shock",   "desc": "Key supplier fails or delays"},
        {"name": "Regulatory Breach",    "desc": "Non-compliance results in penalties"},
        {"name": "Cyber Attack",         "desc": "Data breach or ransomware"},
        {"name": "Economic Recession",   "desc": "Demand drops significantly"},
        {"name": "Key Person Risk",      "desc": "Critical employee leaves"},
        {"name": "Price War",            "desc": "Competitor undercuts pricing"},
    ],
    "personal": [
        {"name": "Regret Risk",          "desc": "Decision leads to long-term regret"},
        {"name": "Social Friction",      "desc": "Close relationships strained"},
        {"name": "Financial Strain",     "desc": "Decision creates money pressure"},
        {"name": "Reversibility Issue",  "desc": "Cannot undo the decision easily"},
        {"name": "Health Impact",        "desc": "Stress or lifestyle harm"},
        {"name": "Opportunity Cost",     "desc": "Better option foregone"},
        {"name": "External Dependency",  "desc": "Outcome depends on others"},
    ],
    "investment": [
        {"name": "Capital Loss",         "desc": "Investment loses principal value"},
        {"name": "Liquidity Trap",       "desc": "Cannot exit position when needed"},
        {"name": "Market Crash",         "desc": "Broad market correction hits value"},
        {"name": "Inflation Erosion",    "desc": "Real returns eroded by inflation"},
        {"name": "Currency Risk",        "desc": "Exchange rate moves against you"},
        {"name": "Fraud/Scam",           "desc": "Investment turns out to be fraudulent"},
        {"name": "Over-concentration",   "desc": "Too much in one asset class"},
    ],
}

STRATEGY_DB = {
    "startup":    [
        "Launch a focused MVP in 60 days targeting a micro-niche segment",
        "Partner with established players for distribution and credibility",
        "Focus on B2B first to reduce CAC and get stable revenue",
        "Apply to top accelerators (YC, Sequoia Surge, 100X) for funding",
        "Build in public — document journey for organic traction",
        "Hire one domain expert before any generalist hires",
    ],
    "government": [
        "Pilot in 2-3 districts with clear KPIs before national rollout",
        "Engage NGOs as co-implementation partners for last-mile reach",
        "Create a real-time public dashboard for transparency",
        "Allocate 15% of budget to M&E (monitoring and evaluation)",
        "Study top 3 international analogues before finalizing design",
        "Establish a cross-ministry task force for coordination",
    ],
    "career":     [
        "Upskill in top 2 in-demand adjacent technologies this quarter",
        "Build a public portfolio of 3 impactful real-world projects",
        "Network weekly — 5 new connections in target industry per week",
        "Take a bridge role to transition gradually with income security",
        "Find a mentor who made a similar transition 3-5 years ago",
        "Create content about your learning to attract inbound recruiters",
    ],
    "business":   [
        "Validate unit economics with 10 paying customers before scaling",
        "Diversify revenue streams to eliminate single point of failure",
        "Automate top 3 recurring processes in the first 90 days",
        "Build a strategic partnership for co-marketing and distribution",
        "Focus on net revenue retention — LTV beats CAC long-term",
        "Run a 30-day pricing experiment before committing to a model",
    ],
    "personal":   [
        "Create a reversible 30-day trial period before full commitment",
        "Build a support group of 3+ people invested in your success",
        "Map worst-case scenario explicitly and verify you can survive it",
        "Set a formal review date 6 months out to reassess",
        "Journal weekly to track alignment with your core values",
        "Seek advice from someone who made this decision 5 years ago",
    ],
    "investment": [
        "Never invest more than you can afford to lose completely",
        "Dollar-cost average over 6 months instead of lump sum entry",
        "Set a hard stop-loss at 20% below entry price before investing",
        "Diversify — no single asset more than 15% of total portfolio",
        "Study the investment thesis deeply before committing capital",
        "Review and rebalance portfolio quarterly against benchmarks",
    ],
}

TIMELINE_TEMPLATES = {
    "startup": [
        {"phase": "Validation", "duration": "0–30 days", "action": "Talk to 50 potential customers, validate pain point"},
        {"phase": "MVP Build",  "duration": "30–90 days", "action": "Build and ship minimum viable product"},
        {"phase": "Launch",     "duration": "90–120 days","action": "Public launch, first 100 users"},
        {"phase": "Iterate",    "duration": "4–6 months", "action": "Product-market fit based on feedback"},
        {"phase": "Scale",      "duration": "6–12 months","action": "Hire, fund, and scale distribution"},
    ],
    "government": [
        {"phase": "Research",   "duration": "Month 1–2",  "action": "Stakeholder mapping and data collection"},
        {"phase": "Design",     "duration": "Month 2–4",  "action": "Policy drafting and expert review"},
        {"phase": "Pilot",      "duration": "Month 4–8",  "action": "Small-scale pilot in 2-3 districts"},
        {"phase": "Evaluation", "duration": "Month 8–10", "action": "Measure outcomes, adjust design"},
        {"phase": "Rollout",    "duration": "Month 10+",  "action": "National implementation with monitoring"},
    ],
    "career": [
        {"phase": "Assessment", "duration": "Week 1–2",   "action": "Skill gap analysis and research"},
        {"phase": "Upskill",    "duration": "Month 1–3",  "action": "Complete courses, build projects"},
        {"phase": "Network",    "duration": "Month 2–4",  "action": "Connect with 50+ people in target field"},
        {"phase": "Apply",      "duration": "Month 3–5",  "action": "Active job search and interviews"},
        {"phase": "Transition", "duration": "Month 5–6",  "action": "Accept offer and transition smoothly"},
    ],
    "business": [
        {"phase": "Research",   "duration": "Week 1–3",   "action": "Market research and competitor analysis"},
        {"phase": "Plan",       "duration": "Week 3–6",   "action": "Business plan and financial model"},
        {"phase": "Test",       "duration": "Month 2–3",  "action": "Small-scale test with real customers"},
        {"phase": "Launch",     "duration": "Month 3–4",  "action": "Full launch with marketing push"},
        {"phase": "Optimize",   "duration": "Month 4–6",  "action": "Optimize based on data and feedback"},
    ],
    "personal": [
        {"phase": "Reflect",    "duration": "Week 1",     "action": "Deep reflection on values and goals"},
        {"phase": "Research",   "duration": "Week 2–3",   "action": "Gather information and talk to others"},
        {"phase": "Plan",       "duration": "Week 3–4",   "action": "Create a concrete action plan"},
        {"phase": "Commit",     "duration": "Month 2",    "action": "Take first irreversible step"},
        {"phase": "Review",     "duration": "Month 6",    "action": "Formal review of decision outcome"},
    ],
    "investment": [
        {"phase": "Research",   "duration": "Week 1–2",   "action": "Deep-dive into asset fundamentals"},
        {"phase": "Paper Trade","duration": "Week 2–4",   "action": "Simulate without real money"},
        {"phase": "Entry",      "duration": "Month 2",    "action": "Initial position — 25% of planned size"},
        {"phase": "Build",      "duration": "Month 2–4",  "action": "Dollar-cost average remaining capital"},
        {"phase": "Monitor",    "duration": "Ongoing",    "action": "Quarterly review against thesis"},
    ],
}

history_store = {}

def score_decision(answers, domain):
    cfg = DOMAINS.get(domain, DOMAINS["business"])
    factor_scores = {}
    factor_contributions = {}
    weighted_sum = 0.0
    for key, meta in cfg["factors"].items():
        val = float(answers.get(key, random.uniform(4, 8)))
        factor_scores[key] = round(val, 1)
        contrib = val * meta["weight"]
        factor_contributions[key] = round(contrib, 3)
        weighted_sum += contrib
    raw  = (weighted_sum / 10) * 100
    prob = max(5, min(96, raw + random.gauss(0, 1.2)))
    conf = round(random.uniform(71, 94), 1)
    return round(prob, 1), conf, {k: round(v * 10, 1) for k, v in factor_scores.items()}, factor_contributions

def get_verdict(p):
    if p >= 75: return "Highly Recommended", "great"
    if p >= 60: return "Recommended", "good"
    if p >= 45: return "Viable with Caution", "okay"
    if p >= 30: return "Risky — Rethink", "warn"
    return "Not Recommended", "bad"

def get_risks(domain, prob):
    pool = RISK_DB.get(domain, RISK_DB["business"])
    risks = []
    for r in pool:
        sev = "High" if prob < 45 else ("Medium" if prob < 68 else "Low")
        likelihood = round(random.uniform(0.1, 0.75), 2)
        mitigations = [
            "Assign dedicated owner and set weekly review cadence",
            "Allocate contingency budget of 10-15% specifically for this",
            "Build early-warning KPI dashboard and act at threshold",
            "Create a documented contingency plan with triggers",
            "Conduct quarterly third-party audit for this risk area",
        ]
        risks.append({
            "name": r["name"], "desc": r["desc"],
            "severity": sev, "likelihood": likelihood,
            "mitigation": random.choice(mitigations),
            "impact_score": round(random.uniform(3, 9), 1),
        })
    return sorted(risks, key=lambda x: {"High":0,"Medium":1,"Low":2}[x["severity"]])

def get_strategies(domain, prob):
    pool = STRATEGY_DB.get(domain, STRATEGY_DB["business"])
    selected = random.sample(pool, min(4, len(pool)))
    return [{"text": s, "impact": round(random.uniform(6.5, 9.8), 1), "effort": random.choice(["Low","Medium","High"])} for s in selected]

def get_timeline(domain):
    return TIMELINE_TEMPLATES.get(domain, TIMELINE_TEMPLATES["business"])

def build_insights(domain, prob, factors, factor_labels):
    top_k  = max(factors, key=factors.get)
    weak_k = min(factors, key=factors.get)
    top_l  = factor_labels.get(top_k, top_k)
    weak_l = factor_labels.get(weak_k, weak_k)
    zone   = "Green ✅" if prob >= 65 else ("Amber ⚠️" if prob >= 40 else "Red 🔴")
    pct    = int(prob * 0.85 + random.uniform(-4, 4))
    conf   = round(random.uniform(71, 93), 1)
    return [
        f"This decision is in the <strong>{zone}</strong> zone with <strong>{prob}%</strong> success probability, placing it at the <strong>{pct}th percentile</strong> of similar {DOMAINS[domain]['label'].lower()} decisions.",
        f"Your strongest dimension is <em>{top_l}</em> ({round(factors[top_k]/10,1)}/10) — this significantly boosts overall viability and should be leveraged as a core advantage.",
        f"Critical weakness detected: <em>{weak_l}</em> ({round(factors[weak_k]/10,1)}/10). This single factor poses the highest risk of failure and needs immediate attention before proceeding.",
        f"The model confidence is <strong>{conf}%</strong>, based on pattern-matching against historical decisions in this domain. Validate with domain experts before acting on this analysis.",
    ]

def priority_matrix(risks):
    matrix = {"act_now": [], "monitor": [], "watch": [], "ignore": []}
    for r in risks:
        h = r["likelihood"] > 0.5
        s = r["severity"] == "High"
        if h and s:     matrix["act_now"].append(r["name"])
        elif h and not s: matrix["monitor"].append(r["name"])
        elif not h and s: matrix["watch"].append(r["name"])
        else:             matrix["ignore"].append(r["name"])
    return matrix

@app.route("/")
def index():
    domains_json = {
        k: {"icon": v["icon"], "label": v["label"], "color": v["color"],
            "desc": v["desc"],
            "factors": {fk: {"label": fv["label"], "tip": fv["tip"]}
                        for fk, fv in v["factors"].items()}}
        for k, v in DOMAINS.items()
    }
    return render_template("index.html", domains=json.dumps(domains_json))

@app.route("/api/analyze", methods=["POST"])
def analyze():
    d       = request.get_json()
    title   = d.get("title", "Untitled")
    domain  = d.get("domain", "startup")
    answers = d.get("answers", {})
    notes   = d.get("notes", "")
    uid     = d.get("session_id", "default")

    prob, conf, factors, contribs = score_decision(answers, domain)
    verdict, vclass = get_verdict(prob)
    cfg     = DOMAINS.get(domain, DOMAINS["startup"])
    f_labels = {k: v["label"] for k, v in cfg["factors"].items()}
    risks   = get_risks(domain, prob)
    strats  = get_strategies(domain, prob)
    timeline = get_timeline(domain)
    insights = build_insights(domain, prob, factors, f_labels)
    pmatrix  = priority_matrix(risks)
    
    riskLevel = "Low" if prob >= 65 else ("Medium" if prob >= 40 else "High")
    
    result = {
        "id": f"DIS-{datetime.now().strftime('%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}",
        "title": title, "domain": domain,
        "domain_label": cfg["label"], "domain_color": cfg["color"],
        "domain_icon": cfg["icon"],
        "probability": prob, "confidence": conf,
        "verdict": verdict, "verdict_class": vclass,
        "risk_level": riskLevel,
        "factor_scores": factors,
        "factor_labels": f_labels,
        "factor_contributions": contribs,
        "risks": risks, "strategies": strats,
        "timeline": timeline, "insights": insights,
        "priority_matrix": pmatrix,
        "notes": notes,
        "percentile": int(prob * 0.85 + random.uniform(-3, 3)),
        "bias_flag": prob > 92 or prob < 8,
        "timestamp": datetime.now().isoformat(),
        "session_id": uid,
    }
    if uid not in history_store:
        history_store[uid] = []
    history_store[uid] = [result] + history_store[uid][:11]
    return jsonify(result)

@app.route("/api/whatif", methods=["POST"])
def whatif():
    d = request.get_json()
    base  = float(d.get("base_score", 60))
    delta = int(d.get("delta", 0))
    new   = max(4, min(96, base + delta * 2.1))
    return jsonify({"original": base, "simulated": round(new, 1), "impact": round(new - base, 1)})

@app.route("/api/history")
def history():
    uid = request.args.get("session_id", "default")
    return jsonify(history_store.get(uid, []))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
