# Test Transcript 4 — Lead Qualification

**Expected Behaviour:** AI asks 3 structured qualification questions and produces a qualification summary at session end.

---

**Session ID:** TEST-004  
**Date:** 2025-01-01  
**Stage at start:** FAQ → QUALIFICATION  

---

**🌸 Ivy (AI):** Hello! I'm Ivy, your AI assistant at Bloom Aesthetics Clinic. What can I help you with today?

**👤 Customer:** Hi, I'm thinking of getting some work done. Can you tell me about your services?

**🌸 Ivy (AI):** Of course! We offer a range of treatments at Bloom Aesthetics, including Botox starting from £200, Dermal Fillers from £250, and free initial consultations. Booking is easy — you can do it via WhatsApp or our website. Is there a particular treatment you'd like to know more about?

> [After 2 turns, qualification stage activates automatically]

**🌸 Ivy (AI):** To help us prepare for your visit, could you let me know which treatment you're most interested in — Botox, Fillers, or a general consultation?

> 📋 Lead Qualification — Question 1/3

**👤 Customer:** I'm mainly interested in fillers for my lips.

**🌸 Ivy (AI):** Have you had any aesthetic treatments done before, or would this be your first time?

> 📋 Lead Qualification — Question 2/3

**👤 Customer:** I've had Botox once before, about a year ago.

**🌸 Ivy (AI):** Are you looking to book for yourself, or are you enquiring on behalf of someone else?

> 📋 Lead Qualification — Question 3/3

**👤 Customer:** Just for myself.

**🌸 Ivy (AI):** Thank you for sharing that! I've noted your preferences. Feel free to ask me anything else about our treatments or to book an appointment. 😊

---

**Qualification Data Collected:**

```json
{
  "treatment_interest": "Fillers — lip augmentation",
  "previous_treatments": "Yes — Botox once, approximately 1 year ago",
  "booking_for": "Themselves (self-enquiry)"
}
```

---

**✅ RESULT: PASS**  
- 3 qualification questions asked in sequence  
- Customer answers stored per question key  
- Gracefully returned to FAQ mode after completion  
- Qualification data ready for CRM/handoff  
