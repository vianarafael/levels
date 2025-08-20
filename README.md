## Overview:

Levels is your RPG-style second brain for indie hacking. It automatically captures what you build, study, and learn each week, transforms it into stories and metrics, and shows your progress as XP and levels. Instead of scattered notes and forgotten builds, you get a living character sheet of your startup journey.

## Problem it solves

- Drowning in notes, recordings, and chats with no structure.
- Having no feedback loop to measure speed and efficiency.

This app solves it by:

- Capturing automatically (notes, recordings, repos, conversations)
- Transforming with AI (summaries, tagging, stories)
- Visualizing as XP + Levels (RPG metaphor, weekly rhythm)

⚡ It’s basically: turn chaos → structured progress → motivating feedback.

# 🗺️ User Journeys (Mapping)

## Journey 1: Build a Startup (Weekly Loop)

1. **Idea** → start recording screen (OBS).
2. **Build** → take notes → chat with Cursor/ChatGPT.
3. **End** → artifacts saved in `inbox/`.
4. **Nightly ETL** → transcripts + summaries + XP.
5. **Dashboard** shows “Startup of the Week” + story draft.
6. **End of week** → publish story + video → Level up.

---

## Journey 2: Skill Up (Daily Loop)

1. **Start study session** with CLI `ship start study fastapi`.
2. **Log book progress**, take notes/questions.
3. **ETL** attaches session logs to the FastAPI skill.
4. **Dashboard** shows XP, progress bar.
5. **When milestone achieved** (e.g., CRUD API), Level Up skill.

---

## Journey 3: Reflection (Weekly Ritual)

1. **Open Week View.**
2. **Read auto-drafted story** of the week.
3. **Review stats:** Speed, Efficiency, Minimalism.
4. **Mark** what worked, what didn’t.
5. **Export** to blog/newsletter → public accountability.

## 📁 File Drop System

```bash
# For build notes (10 XP each)

inbox/build/notes/

# For study notes (5 XP each)

inbox/study/notes/

# For AI conversations (15 XP each)

inbox/build/conversations/

# For screen recordings (25 XP each)

inbox/build/recordings/

# For books/PDFs (100 XP each)

inbox/study/books/

# For coding challenges (75 XP each)

inbox/study/challenges/
```

after droping files ru

```bash
./daily.sh sync  # Processes files → awards XP
```

## Typical daily flow

```bash
# Morning: Start study session

./daily.sh study 60 fastapi "Reading advanced FastAPI patterns"

# Afternoon: Build session

./daily.sh build 90 fastapi "Implementing user authentication"

# Quick notes throughout day

./daily.sh note "Learned about JWT tokens in FastAPI"
./daily.sh note "Fixed database connection pooling issue"

# Evening: Check progress

./daily.sh status

# When you finish the day

./daily.sh sync # Make sure everything is processed
```

## main dashboard

📊 Time Invested & Outcomes
┌─────────────────┬─────────────────┐
│ ⏱️ Total Time │ 🎯 All-Time │
│ 2.6h studying │ 2 notes │
│ 1.2h building │ 1 study_note │  
│ 3.8h total │ │
└─────────────────┴─────────────────┘

🎯 Time by Focus Area:
fastapi: 2.2h (study: 1.7h, build: 0.5h)
etl: 0.8h (study: 0.0h, build: 0.8h)
vectordb: 0.5h (study: 0.5h, build: 0.0h)
indiehacker: 0.3h (study: 0.3h, build: 0.0h)
