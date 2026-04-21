# ==========================================================
# 🎓 NARYAN AI — SUBJECT DETECTOR
#    Automatically infers the engineering subject from text.
# ==========================================================

import re
from typing import Optional

SUBJECT_MAP = {
    "mathematics 1":  [
        r"math\s*1", r"maths?\s*[i1]", r"calculus", r"differential equation",
        r"integration", r"differentiation", r"laplace", r"matrix", r"determinant",
        r"fourier series", r"partial differential",
    ],
    "mathematics 2":  [
        r"math\s*2", r"maths?\s*(ii|2)", r"complex number", r"z.transform",
        r"numerical method", r"probability", r"statistics",
    ],
    "physics":  [
        r"physics", r"optics", r"quantum", r"thermodynamics", r"wave",
        r"electromagnetism", r"newton", r"gravitation", r"relativity",
        r"semiconductor", r"photon",
    ],
    "basic electrical engineering":  [
        r"electrical", r"circuit", r"ohm", r"kirchhoff", r"resistor",
        r"capacitor", r"inductor", r"voltage", r"current", r"power factor",
        r"transformer", r"ac circuit", r"dc circuit",
    ],
    "introduction to electrical engineering":  [
        r"intro.*electrical", r"basic circuit", r"signal", r"diode", r"transistor",
    ],
    "introduction to mechanical engineering":  [
        r"mechanical", r"thermodynamics", r"fluid", r"statics", r"dynamics",
        r"machine", r"gear", r"torque", r"stress", r"strain", r"beam",
    ],
}


def detect_subject(text: str) -> Optional[str]:
    """
    Return the most likely subject name, or None if no match found.
    Matching is prioritised by number of pattern hits.
    """
    text_lower = text.lower()
    scores = {}
    for subject, patterns in SUBJECT_MAP.items():
        score = sum(1 for p in patterns if re.search(p, text_lower))
        if score:
            scores[subject] = score
    if not scores:
        return None
    return max(scores, key=scores.get)
