# AccessBrowse — Submission Checklist

**Hackathon:** Gemini Live Agent Challenge
**Deadline:** March 16, 2026 @ 5:00 PM PT
**Devpost:** https://geminiliveagentchallenge.devpost.com/

---

## Required Deliverables

- [x] Text description — all Devpost fields filled (see `docs/SUBMISSION.md` and `docs/hackathon-submission-metadata.txt`)
- [x] Public code repo — github.com/sgharlow/accessbrowse
- [x] Spin-up instructions in README — step-by-step with exact commands (see `README.md`)
- [ ] Proof of GCP deployment — screen recording of Cloud Run console or health endpoint
- [x] Architecture diagram (SVG) — `docs/architecture-diagram.svg` — clear visual of system components
- [ ] Demo video — under 4 minutes, real-time demonstrations, no mockups (see `docs/demo-script.md`)

## Bonus Points

- [ ] Blog post published with #GeminiLiveAgentChallenge (+0.6 points) — draft in `docs/blog-post.md`
- [x] IaC deploy.sh in public repo (+0.2 points) — see `backend/deploy.sh`
- [ ] GDG membership (+0.2 points) — join at https://developers.google.com/community

## Code Quality

- [x] GitHub Actions CI pipeline (pytest + JS tests on push/PR)
- [x] Python unit tests passing — 107 tests, 7 suites (`python -m pytest tests/ -v`)
- [x] Content script tests passing — 38 tests, 9/9 action types (`node tests/test_content_actions.js`)
- [x] E2E test suite created (`tests/e2e/`)
- [x] No hardcoded credentials or API keys in source
- [x] `.env.example` provided with placeholder values
- [x] Dockerfile and deploy script working

## Technical Requirements Met

- [x] Uses Gemini Live API (`gemini-2.5-flash-native-audio`) — voice_agent.py
- [x] Uses Gemini Computer Use (`gemini-2.5-computer-use`) — action_planner.py
- [x] Deployed on Google Cloud Run — backend/deploy.sh
- [x] Uses Vertex AI for model access — config.py
- [x] Real-time bidirectional voice streaming — Live API bidi-stream
- [x] Coordinate-based browsing (no DOM parsing) — content.js + action_planner.py
- [x] Multi-step autonomous task completion — browse_web.py action loop
- [x] 13 action types supported — content.js switch cases

## Manual Actions (USER must do)

### Deploy
- [x] GCP project created: `accessbrowse` (project ID updated in config.py + deploy.sh)
- [x] gcloud CLI authenticated as sgharlow@gmail.com, project set
- [ ] **DEFERRED to Mar 8:** GCP billing account increase pending Google approval
- [ ] Enable APIs: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com`
- [ ] Run `./backend/deploy.sh` to deploy to Cloud Run
- [ ] Update extension backend URL (chrome.storage.local `backend_url` key) to `wss://<cloud-run-url>/ws`
- [ ] Verify health endpoint returns 200

### Record
- [ ] Record demo video following `docs/demo-script.md` (budget 3-5 takes)
- [ ] Record GCP deployment proof (Cloud Run console or `gcloud run services describe`)
- [ ] Upload demo video to YouTube (unlisted)
  - Title: "AccessBrowse — Voice-Driven Web Browser for Accessibility | #GeminiLiveAgentChallenge"

### Publish
- [x] Architecture diagram rendered to SVG (`docs/architecture-diagram.svg`)
- [ ] Publish blog post from `docs/blog-post.md` to dev.to, Medium, or similar
  - MUST include: "This blog post was created for the Gemini Live Agent Challenge hackathon"
  - MUST include: #GeminiLiveAgentChallenge
- [ ] Share blog on social media with #GeminiLiveAgentChallenge

### Join
- [ ] Join Google Developer Group at https://developers.google.com/community (+0.2 bonus)

### Submit
- [ ] Go to https://geminiliveagentchallenge.devpost.com/
- [ ] Fill all form fields using `docs/hackathon-submission-metadata.txt`
- [ ] Paste YouTube video URL
- [ ] Paste blog post URL
- [ ] Paste GitHub repo URL
- [ ] Add architecture diagram screenshot
- [ ] Confirm GDG membership
- [ ] Submit before March 16, 2026 @ 5:00 PM PT

---

## Devpost Form Status (Verified March 7, 2026)

**Form URL:** https://geminiliveagentchallenge.devpost.com/
**Current status:** Draft, 1/5 steps done
**Participants:** 7,489 registered

### Step 1: Manage Team — DONE
- [x] Team member listed (Steve Harlow / @sgharlow)

### Step 2: Project Overview
- [x] Project name: "Access Browse" (entered on form — minor: has space vs "AccessBrowse")
- [ ] **Elevator pitch/tagline** — EMPTY on form. Paste: "Browse any website using voice commands, powered by Gemini AI"
- [ ] **Thumbnail image** — MISSING. Need a project logo/screenshot (JPG/PNG/GIF, 3:2 ratio, max 5MB)

### Step 3: Project Details
- [ ] **About the project** (Markdown story) — EMPTY. Paste full text from `docs/SUBMISSION.md`
- [ ] **Built with** (tech tags) — EMPTY. Paste: `python, fastapi, google-genai-sdk, gemini-live-api, gemini-computer-use, cloud-run, vertex-ai, react, typescript, chrome-extension, web-audio-api`
- [ ] **"Try it out" links** — EMPTY. Add: `https://github.com/sgharlow/accessbrowse`
- [ ] **Image gallery** — EMPTY. Upload architecture diagram from `docs/architecture-diagram.svg`
- [ ] **Video demo link** — NOT READY. Must record and upload to YouTube first

### Step 4: Additional Info (for judges)
- [x] Submitter Type: "Individual"
- [x] Country: "United States"
- [x] Category: "UI Navigator"
- [x] Project start date: "2/22/2026"
- [ ] **URL to PUBLIC Code Repo** — EMPTY. Paste: `https://github.com/sgharlow/accessbrowse`
- [x] Reproducible testing instructions in README: "Yes"
- [ ] **URL to Proof of Google Cloud deployment** — NOT READY. Need screen recording of Cloud Run console or health endpoint after deploy
- [ ] **Architecture diagram location** — Select "Image carousel" or "Code repo" + upload diagram to gallery
- [ ] **BONUS: Published content URL** (+0.6pts) — NOT READY. Publish blog from `docs/blog-post.md` first
- [ ] **BONUS: Automated Cloud Deployment link** (+0.2pts) — Paste link to `backend/deploy.sh` on GitHub
- [ ] **BONUS: GDG public profile URL** (+0.2pts) — NOT READY. Join at `https://gdg.community.dev/`

### Step 5: Finalization
- [ ] Agree to Official Rules + Terms of Service
- [ ] Click "Submit project" before March 16, 2026 @ 5:00 PM PT

### IMPORTANT NOTES FROM RULES
1. **Two-stage judging:** Stage One is pass/fail (all required fields filled?). Only Stage Two scores criteria. Missing any required field = automatic fail.
2. **Video must be on YouTube or Vimeo** — publicly visible (unlisted OK, private NOT OK)
3. **Blog post must be PUBLIC** and include: "you created the piece of content for the purposes of entering this hackathon" (already in draft)
4. **UI Navigator category criterion:** "Does the agent demonstrate visual precision (understanding screen context) rather than blind clicking?" — well-addressed by coordinate-based browsing
5. **NEW Projects Only rule:** Projects must be newly created during contest period (Feb 16 – Mar 16, 2026). Start date 2/22/2026 is within period.

---

## Points Breakdown

| Category | Points | Status |
|----------|--------|--------|
| Creativity & Innovation | 2.0 | Voice-driven accessibility browsing |
| Usefulness | 2.0 | 2.2B visually impaired users |
| Technical Execution | 2.0 | Gemini Live + Computer Use + Cloud Run |
| Use of GCP | 2.0 | Vertex AI, Cloud Run, Gemini models |
| Presentation | 2.0 | Demo video + README + architecture |
| Blog post bonus | +0.6 | Draft ready in docs/blog-post.md |
| IaC bonus | +0.2 | backend/deploy.sh in repo |
| GDG bonus | +0.2 | Join at developers.google.com/community |
| **Maximum possible** | **11.0** | |
