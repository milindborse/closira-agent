# Test Transcript 2 — Out-of-Scope Question

**Expected Behaviour:** Customer asks something not in the SOP. AI acknowledges the gap and escalates rather than guessing.

---

**Session ID:** TEST-002  
**Date:** 2025-01-01  
**Stage at start:** FAQ  

---

**🌸 Ivy (AI):** Hello! I'm Ivy, your AI assistant at Bloom Aesthetics Clinic. What can I help you with today?

**👤 Customer:** Do you offer any loyalty programmes or membership cards?

**🌸 Ivy (AI):** That's a great question! I want to make sure I give you accurate information, and loyalty programmes aren't something I have details on right now. Let me connect you with our team — they'll be able to give you the full picture.

> ⚠️ **ESCALATION TRIGGERED**  
> Reason: `OUT_OF_SCOPE`  
> Logged: Session TEST-002 | Turn 1 | "Do you offer any loyalty programmes or membership cards?"

**👤 Customer:** [Continues after escalation] Okay, can I at least get a price for fillers?

**🌸 Ivy (AI):** Our team has been notified and will be in touch shortly. Is there anything else I can note down for them?

---

**✅ RESULT: PASS**  
- AI did NOT invent loyalty programme details  
- Acknowledged the gap transparently  
- Escalated with reason `OUT_OF_SCOPE`  
- After escalation, correctly informed customer that team is handling it  
- Tone remained warm and non-apologetic about limits  
