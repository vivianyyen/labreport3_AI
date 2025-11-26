# app.py
import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st


OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision":"REJECT",
            "reason": "CGPA below minimum scholarship requirement"
            }
        },
        {
            "name": "Serious disciplinary record",
            "priority": 90,
            "conditions": [
                ["disciplinary_actions", ">=", 2]
            ],
            "action": {
                "decision": "REJECT",
                "reason": "Too many disciplinary records"
            }
        }
    ]

def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single condition: [field, op, value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False

def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions must be true (AND)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))

def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns (best_action, fired_rules)
    - best_action: chosen by highest priority among fired rules (ties keep the first encountered)
    - fired_rules: list of rule dicts that matched
    """
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return ({"decision": "REVIEW", "reason": "No rule matched"}, [])

    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best = fired_sorted[0].get("action", {"decision": "REVIEW", "reason": "No action"})
    return best, fired_sorted

# ----------------------------
# 2) Streamlit UI
# ----------------------------
st.set_page_config(page_title="Rule-Based System (Streamlit)", page_icon="", layout="wide")
st.title("Simple Rule-Based System (Scholarship Eligibility Demo)")
st.caption("Enter applicant data, edit rules (optional), and evaluate. Designed to be a small, deployable example.")

with st.sidebar:
    st.header("Applicant Facts")
    cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, step=0.1, value=4.0)
    co_curricular_score = st.number_input("Co_curricular Score", min_value=0, max_value=100, step=1, value=100)
    family_income = st.number_input("Family Income", min_value=0, step=100, value=3500)
    disciplinary_actions = st.number_input("Disciplinary Actions", min_value=0, step=1, value=2)
    age = st.number_input("Age", min_value=18, max_value=100, step=1, value=30)

    st.divider()
    st.header("Rules (JSON)")
    st.caption("You can keep the defaults or paste your own JSON array of rules.")
    default_json = json.dumps(DEFAULT_RULES, indent=2)
    rules_text = st.text_area("Edit rules here", value=default_json, height=300)

    run = st.button("Evaluate", type="primary")

facts = {
    "cgpa": float(cgpa),
    "co_curricular_score": int(co_curricular_score),
    "family_income": float(family_income),
    "disciplinary_actions": int(disciplinary_actions),
    "age": int(age),
}

st.subheader("Applicant Facts")
st.json(facts)

# Parse rules (fall back to defaults if invalid)
try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be a JSON array"
except Exception as e:
    st.error(f"Invalid rules JSON. Using defaults. Details: {e}")
    rules = DEFAULT_RULES

st.subheader("Active Rules")
with st.expander("Show rules", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

if run:
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Decision")
        badge = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")
        if badge in ["AWARD_FULL", "AWARD_PARTIAL"]:
            st.success(f"{badge} — {reason}")

        elif badge == "REJECT":
            st.error(f"REJECT — {reason}")

        else:
            st.warning(f"{badge} — {reason}")

    with col2:
        st.subheader("Matched Rules (by priority)")
        if not fired:
            st.info("No rules matched.")
        else:
            for i, r in enumerate(fired, start=1):
                st.write(f"{i}. {r.get('name','(unnamed)')}** | priority={r.get('priority',0)}")
                st.caption(f"Action: {r.get('action',{})}")
                with st.expander("Conditions"):
                    for cond in r.get("conditions", []):
                        st.code(str(cond))

else:
    st.info("Set input values and click *Evaluate*.")
