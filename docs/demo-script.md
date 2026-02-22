# AccessBrowse — Demo Video Script

**Target length:** Under 4 minutes (3:55)
**Format:** Screen recording with voiceover
**Requirements:** Backend MUST be running on Cloud Run (not localhost). All demos are live, real-time interactions. No mockups, no pre-recorded responses.
**Tips:** Budget 3-5 recording attempts. Live AI demos are unpredictable. Pick the best take.

---

## 0:00 - 0:30 — Problem + Pitch (30 seconds)

**[Screen: Title slide or website hero image]**

> "Over 2.2 billion people worldwide have some form of visual impairment. Yet the web is built for eyes — buttons to find, layouts to scan, forms to fill in. Screen readers help with text, but they struggle with the modern web: dynamic single-page apps, JavaScript-heavy layouts, and interactive elements that only make sense visually."

**[Screen: Brief montage of complex web pages — Zillow, Amazon, CNN]**

> "What if you could browse any website just by talking? That's AccessBrowse."

---

## 0:30 - 0:50 — Architecture Overview (20 seconds)

**[Screen: Architecture diagram (screenshots/architecture.png)]**

> "Here's how it works. A Chrome extension captures your voice and sends it over a WebSocket to our FastAPI backend on Cloud Run. The backend connects to Gemini Live API for real-time voice conversation and Gemini Computer Use for visual understanding. When you ask to browse a site, Gemini analyzes screenshots of your browser and returns precise coordinates for every click, type, and scroll — working on any website, no special configuration needed."

**[Point to key components as you mention them]**

---

## 0:50 - 2:10 — Live Demo 1: Apartment Search on Zillow (80 seconds)

**[Screen: Chrome browser with AccessBrowse sidepanel open]**

> "Let me show you. I'll open the AccessBrowse sidepanel and start a session."

**[Click "Start Session" — wait for "Connected — listening..." status]**

> "Watch the status — we're now connected to Gemini Live API via Cloud Run."

**[Click "Speak" button]**

> *Speak into mic:* "Search for apartments in Seattle under $1000 on Zillow."

**[Let AccessBrowse work — narrate what's happening as it proceeds]**

> "Watch the sidepanel — you can see real-time status updates as the system works. It's navigating to Zillow... now it's analyzing the page with Gemini Computer Use... it found the search box and is typing the query... now it's looking at the results."

**[Wait for Gemini to read back results — let the 24kHz voice output play]**

> "There it is — Gemini just read back the top results with prices and locations. Notice the voice quality — that's 24kHz audio, noticeably clearer than standard 16kHz. The transcript updates in real-time in the sidepanel."

**[Briefly show the transcript in the sidepanel]**

---

## 2:10 - 3:10 — Live Demo 2: Shopping on Amazon (60 seconds)

**[Screen: Still in the same session]**

> "Let's try something more complex — shopping."

**[Click "Speak"]**

> *Speak into mic:* "Find noise-canceling headphones on Amazon."

**[Let AccessBrowse work through the multi-step flow]**

> "This is a multi-step task — it needs to navigate to Amazon, search for headphones, and then read through the results. Each step is a separate screenshot analysis by Gemini Computer Use, followed by a coordinate-based action in the browser."

**[While waiting, point out the step counter in status messages]**

> "You can see the step-by-step status: 'Step 1: analyzing page,' 'Step 2: clicking search box,' 'Step 3: typing query.' The system handles up to 10 steps per browse action."

**[Wait for results to be read back]**

> "And there are the top results — with product names and prices read aloud."

**[Optional: demonstrate barge-in by speaking while Gemini is still talking]**

> "I can also interrupt at any time — that's barge-in handling from the Live API."

---

## 3:10 - 3:40 — Live Demo 3: News Headlines on CNN (30 seconds)

**[Screen: Same session, continuing]**

> "One more. Let's read some news."

**[Click "Speak"]**

> *Speak into mic:* "Read me today's top headlines on CNN."

**[Let AccessBrowse navigate to CNN and use read_page tool]**

> "This time AccessBrowse is using the read_page tool, which asks Gemini Computer Use to generate an accessibility-focused summary of the page — describing what's on screen in natural language, organized by sections."

**[Let Gemini read the headlines aloud]**

---

## 3:40 - 3:55 — Summary (15 seconds)

**[Screen: Architecture diagram or summary slide]**

> "AccessBrowse: voice-driven web browsing for accessibility. Built with Gemini Live API for real-time voice, Gemini Computer Use for coordinate-based browsing, deployed on Cloud Run. 13 action types, any website, no configuration needed. Making the web accessible through conversation."

**[End]**

---

## Recording Checklist

- [ ] Backend is deployed and running on Cloud Run (not localhost)
- [ ] Extension is loaded and pointing to production URL
- [ ] Microphone is working and audio levels are good
- [ ] Screen recording software is capturing both browser and audio
- [ ] Sidepanel is visible and transcript area is clear
- [ ] No sensitive information visible in browser (bookmarks, tabs, etc.)
- [ ] Internet connection is stable
- [ ] Close unnecessary browser tabs to reduce visual clutter
- [ ] Test one voice command before starting the real recording
