## Overview

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

