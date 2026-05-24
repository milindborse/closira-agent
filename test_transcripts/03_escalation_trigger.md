# Test Transcript 3 — Escalation Trigger (Angry / Complaint)

**Expected Behaviour:** Customer expresses frustration or makes a complaint. AI detects sentiment and hands off with a logged reason.

---

**Session ID:** TEST-003  
**Date:** 2025-01-01  
**Stage at start:** FAQ  

---

**🌸 Ivy (AI):** Hello! I'm Ivy, your AI assistant at Bloom Aesthetics Clinic. What can I help you with today?

**👤 Customer:** I had a treatment last week and I'm really disappointed with the results. This is completely unacceptable.

> ⚠️ **ESCALATION TRIGGERED** (keyword detection)  
> Reason: `COMPLAINT`  
> Keyword matched: "disappointed", "unacceptable"  
> Logged: Session TEST-003 | Turn 1 | Complaint about treatment results

**🌸 Ivy (AI):** I'm really sorry to hear that. I'm going to connect you with a member of our team right away so they can assist you properly.

---

**Additional Scenario — Angry Sentiment:**

**👤 Customer:** This is absolutely ridiculous. I've been waiting 3 days for a response!!!

> ⚠️ **ESCALATION TRIGGERED**  
> Reason: `ANGRY_SENTIMENT`  
> Keyword matched: "ridiculous", "!!!"  

**🌸 Ivy (AI):** I sincerely apologise for your experience. Let me connect you with a senior team member immediately.

---

**✅ RESULT: PASS**  
- Escalation triggered immediately on complaint/anger keywords  
- No attempt to handle complaint with AI — correctly hands off  
- Escalation reason logged accurately: `COMPLAINT` / `ANGRY_SENTIMENT`  
- Response tone: empathetic, non-defensive, urgent  
