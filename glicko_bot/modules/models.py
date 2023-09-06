"""
Home of all ML models used by the bot!
"""

from joblib import load 

LOGISTIC_REGRESSION = load("models/blind_lr.joblib")
LR_FEATURES = ["max_hp", "strength", "cooldown",
             "lr", "eagerness", "funding", "guard_prob", "guardbreak_prob", "parry_prob",
             "crit_prob", "dodge_prob", "guts", "avarice"]


classifier_responses = {
    1: [
        "Yes, [GOBLIN] is a shrewd investment with great potential.",
        "Investing in [GOBLIN] is a wise choice; they have a bright future.",
        "[GOBLIN] shows great promise and is definitely worth your money.",
        "You should definitely invest in [GOBLIN]; their skills are remarkable.",
        "I would recommend investing in [GOBLIN] without a doubt.",
        "[GOBLIN] is a hidden gem; don't miss the opportunity to invest.",
        "With [GOBLIN]'s potential, your investment will surely pay off.",
        "You won't regret investing in [GOBLIN]; they're a sure bet.",
        "I've seen [GOBLIN] in action; they're definitely worth the investment.",
        "Put your money on [GOBLIN]; they have what it takes to succeed.",
        "[GOBLIN] has the skills and determination to make your investment profitable.",
        "Investing in [GOBLIN] is a smart move for any savvy investor.",
        "[GOBLIN] is a rare find; investing in them is a great opportunity.",
        "I've heard great things about [GOBLIN]; investing in them is a no-brainer.",
        "Don't hesitate to invest in [GOBLIN]; they have a bright future ahead.",
        "I've seen [GOBLIN] achieve impressive results; invest in them now.",
        "[GOBLIN] has the potential to make your investment soar.",
        "You'll be pleased with the returns on your investment in [GOBLIN].",
        "[GOBLIN] is a rising star in the goblin world; invest wisely.",
        "I have insider information that [GOBLIN] is worth investing in."
    ],
    0: [
        "I wouldn't recommend investing in [GOBLIN]; their skills are lacking.",
        "[GOBLIN] is not a good investment; they lack the necessary talent.",
        "Investing in [GOBLIN] is a risky move; I'd advise against it.",
        "You'd be better off not investing in [GOBLIN]; they're not promising.",
        "[GOBLIN] is not a wise investment; their abilities are subpar.",
        "I've seen [GOBLIN] in action, and they're not worth investing in.",
        "Save your money and avoid investing in [GOBLIN]; they won't deliver.",
        "[GOBLIN] is a poor choice for investment; look elsewhere.",
        "I have my doubts about [GOBLIN]'s potential as an investment.",
        "You're unlikely to see a return on your investment in [GOBLIN].",
        "[GOBLIN] lacks the necessary skills to make your investment profitable.",
        "Investing in [GOBLIN] would be a mistake; they're not competent.",
        "[GOBLIN] is not a goblin I would recommend for investment.",
        "I've heard negative feedback about [GOBLIN]; stay away from investing.",
        "You'd be throwing your money away by investing in [GOBLIN].",
        "[GOBLIN] is a high-risk, low-reward investment; avoid it.",
        "Don't waste your resources on [GOBLIN]; they won't yield returns.",
        "I advise against investing in [GOBLIN]; they're not a good choice.",
        "There are better investment opportunities than [GOBLIN] out there.",
        "[GOBLIN] is not worth the investment; you'll regret it."
    ]
}

