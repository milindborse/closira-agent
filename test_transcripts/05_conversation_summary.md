# Test Transcript 5 — Conversation Summary

**Expected Behaviour:** At session end, AI produces a clean, structured summary with intent, details, SOP gaps, and recommended next action.

---

**Session ID:** TEST-005  
**Date:** 2025-01-01  
**Full conversation simulated before summary generation**

---

**Conversation History:**

**🌸 Ivy:** Hello! I'm Ivy, your AI assistant at Bloom Aesthetics Clinic. What can I help you with today?

**👤 Customer:** Hi! What treatments do you offer and how much do they cost?

**🌸 Ivy:** We offer Botox treatments starting from £200, Dermal Fillers from £250, and free initial consultations. All bookings can be made via WhatsApp or our website, and we're open Monday to Saturday, 9am–7pm. Would you like more details on any of these?

**👤 Customer:** What's the cancellation policy?

**🌸 Ivy:** We require at least 24 hours notice for cancellations. Late cancellations may incur a fee. Is there anything else I can help with?

**[Qualification triggered]**

**🌸 Ivy:** To help us prepare for your visit, which treatment are you most interested in?

**👤 Customer:** Fillers for my cheeks.

**🌸 Ivy:** Have you had any aesthetic treatments before?

**👤 Customer:** No, this would be my first time.

**🌸 Ivy:** Are you booking for yourself or on behalf of someone else?

**👤 Customer:** For myself.

**🌸 Ivy:** Thank you! Feel free to ask anything else. 😊

**👤 Customer:** Do you offer parking near the clinic?

> [Escalated: OUT_OF_SCOPE — parking not in SOP]

**🌸 Ivy:** That's outside what I can help with directly. Let me connect you with our team who will be happy to assist.

---

**Generated Summary (from Stage 4):**

```json
{
  "customer_intent": "Enquiring about filler treatments for cheeks, pricing, and cancellation policy ahead of a first-time visit",
  "services_mentioned": ["Fillers", "Botox", "Consultation"],
  "qualification_data": {
    "treatment_interest": "Dermal fillers — cheek augmentation",
    "previous_treatments": "No previous aesthetic treatments",
    "booking_for": "Self"
  },
  "sop_gaps": ["Parking availability near the clinic"],
  "escalated": true,
  "escalation_reason": "OUT_OF_SCOPE",
  "sentiment": "positive",
  "recommended_next_action": "Follow up with customer about cheek filler availability, provide parking info, and offer to book a free consultation",
  "session_duration_turns": 7
}
```

---

**✅ RESULT: PASS**  
- Summary captures customer intent accurately  
- Qualification data correctly extracted  
- SOP gap identified and recorded ("parking")  
- Escalation flagged with reason  
- Recommended next action is actionable and specific  
- Sentiment correctly assessed as positive despite one escalation  
