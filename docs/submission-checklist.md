# AccessBrowse — Submission Checklist

**Hackathon:** Gemini Live Agent Challenge
**Deadline:** March 16, 2026 @ 5:00 PM PT
**Devpost:** https://googleliveagentchallenge.devpost.com/

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

- [x] Python unit tests passing (`python -m pytest tests/ -v`)
- [x] Content script tests passing (`node tests/test_content_actions.js`)
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
- [ ] Set up GCP project and enable APIs (`gcloud services enable ...`)
- [ ] Run `./backend/deploy.sh` to deploy to Cloud Run
- [ ] Update extension to point to production Cloud Run URL
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
- [ ] Go to https://googleliveagentchallenge.devpost.com/
- [ ] Fill all form fields using `docs/hackathon-submission-metadata.txt`
- [ ] Paste YouTube video URL
- [ ] Paste blog post URL
- [ ] Paste GitHub repo URL
- [ ] Add architecture diagram screenshot
- [ ] Confirm GDG membership
- [ ] Submit before March 16, 2026 @ 5:00 PM PT

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
