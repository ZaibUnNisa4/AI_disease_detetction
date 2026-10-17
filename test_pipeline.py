from pipeline import InfectiousDiseaseSystem

s = InfectiousDiseaseSystem()

print("--- Test Patient Predictions ---\n")
tests = [
    (28, "Male",   4,  True,  "4-day fever with rash      -> Expected: Dengue"),
    (45, "Female", 14, False, "14-day fever no rash       -> Expected: Typhoid"),
    (19, "Male",   3,  True,  "3-day fever with rash      -> Expected: Dengue"),
    (60, "Female", 10, False, "10-day fever no rash       -> Expected: Typhoid"),
]

for age, gender, dur, rash, desc in tests:
    r = s.screen_patient(age, gender, dur, rash)
    d = r["clinical_diagnosis"]
    probs = d["probabilities"]
    print(desc)
    print("  Prediction : " + d["predicted_disease"])
    print("  Confidence : " + str(round(d["confidence"] * 100, 1)) + "%")
    print("  Dengue prob: " + str(round(probs.get("Dengue", 0) * 100, 1)) + "%")
    print("  Typhoid prob:" + str(round(probs.get("Typhoid", 0) * 100, 1)) + "%")
    print()
