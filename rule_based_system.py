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
            "decision": "REJECT",
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
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))


def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    fired = [r for r in rules if rule_matches(facts, r)]

    if not fired:
        return ({"decision": "REVIEW", "reason": "No rule matched"}, [])

    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best = fired_sorted[0]["action"]
    return best, fired_sorted


## Streamlit UI

st.set_page_config(page_title="Scholarship Rule-Based System", page_icon="", layout="wide")
st.title("🎓 Scholarship Advisory Rule-Based System")
st.caption("Enter applicant data, edit rules (optional), and evaluate eligibility.")

with st.sidebar:
    st.header("Applicant Information")

    cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, step=0.01, value=3.2)
    co_curricular_score = st.number_input("Co-curricular Score (0–100)", min_value=0, max_value=100, value=70)
    family_income = st.number_input("Family Monthly Income (MYR)", min_value=0, step=100, value=5000)
    disciplinary_actions = st.number_input("Number of Disciplinary Actions", min_value=0, max_value=10, value=0)

    st.divider()
    st.header("Scholarship Rules (JSON)")
    default_json = json.dumps(DEFAULT_RULES, indent=2)
    rules_text = st.text_area("Edit rules here", value=default_json, height=300)

    run = st.button("Evaluate", type="primary")

facts = {
    "cgpa": float(cgpa),
    "co_curricular_score": int(co_curricular_score),
    "family_income": float(family_income),
    "disciplinary_actions": int(disciplinary_actions)
}

st.subheader("Applicant Facts")
st.json(facts)

# Load rules safely
try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list)
except Exception as e:
    st.error(f"Invalid rules JSON. Using default scholarship rules. Error: {e}")
    rules = DEFAULT_RULES

st.subheader("Active Rules")
with st.expander("Show rules", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

# Run evaluation
if run:
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Final Scholarship Decision")
        decision = action["decision"]
        reason = action["reason"]

        if decision == "AWARD_FULL":
            st.success(f"FULL SCHOLARSHIP — {reason}")
        elif decision == "AWARD_PARTIAL":
            st.info(f"PARTIAL SCHOLARSHIP — {reason}")
        elif decision == "REJECT":
            st.error(f"REJECT — {reason}")
        else:
            st.warning(f"REVIEW — {reason}")

    with col2:
        st.subheader("Matched Rules (Highest Priority First)")
        if not fired:
            st.info("No rules matched.")
        else:
            for i, r in enumerate(fired, start=1):
                st.write(f"**{i}. {r['name']}** | priority={r['priority']}")
                st.caption(f"Action: {r['action']}")
                with st.expander("Conditions"):
                    for cond in r["conditions"]:
                        st.code(str(cond))
else:
    st.info("Enter values and click **Evaluate** to determine scholarship eligibility.")
