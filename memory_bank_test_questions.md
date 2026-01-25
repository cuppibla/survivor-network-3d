
# 🧠 Memory Bank Test Questions

Use these scenarios to verify that the Agent Engine is correctly remembering your preferences and context.

The Agent Engine is configured to remember:
1.  **Search Preferences** (Methods, filters, specific skills, locations)
2.  **Urgent Needs Context** (Resources monitoring, critical situations)

---

## 🧪 Scenario 1: Search Preferences (Biome & Method)

**Goal:** Teach the agent your preferred location and search style, then verify it applies them automatically.

**Step 1: Establish Context**
> "I generally prefer using semantic search because I don't know the exact skill names. Also, I'm mostly focused on survivors living in the **Forest Biome**."

*(The agent should acknowledge this)*

**Step 2: Verify Memory (Same Session or New Session)**
> "Find me someone who is good at building structures."

**Expected Behavior:**
- The agent should use `semantic_search`.
- The agent might automatically apply a filter for `biome='Forest'`, or at least mention that it's looking in the Forest Biome based on your preference.

---

## 🧪 Scenario 2: Urgent Needs Monitoring

**Goal:** Tell the agent you are tracking a specific crisis, then refer to it vaguely.

**Step 1: Establish Context**
> "I am very concerned about the **medicine shortage** in the **Northern Camp**. Please keep track of that for me."

*(The agent records this interest)*

**Step 2: Verify Memory**
> "Any updates on the situation I mentioned?"
> *OR*
> "Who can help with the crisis?"

**Expected Behavior:**
- The agent should understand "the situation" refers to the **medicine shortage**.
- It should look for doctors or medical supplies, specifically in or for the Northern Camp.

---

## 🧪 Scenario 3: Skill Preferences

**Goal:** Express a specific interest in a type of survivor.

**Step 1: Establish Context**
> "I'm always on the lookout for survivors with **Leadership** skills or anyone who was a **Doctor** before."

**Step 2: Verify Memory (New Session)**
> "Who should I recruit next?"

**Expected Behavior:**
- The agent should recommend survivors who fit your "Leadership" or "Doctor" preference, citing your history.

---

## ⚙️ How to Verify

1.  **Run the Backend:** Ensure the backend is running with `USE_MEMORY_BANK=TRUE` in `.env`.
2.  **Check Logs:** Look for logs indicating `PreloadMemoryTool` is active.
3.  **Inspect Agent Output:** The agent might explicitly say "Remembering your preference for..." or implicitly apply it.
