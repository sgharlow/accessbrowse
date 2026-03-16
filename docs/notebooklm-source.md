# AccessBrowse: Voice-Driven Web Browsing for Accessibility

## Project Summary for NotebookLM Video Script (~3 minutes)

This document describes AccessBrowse, a submission for the Gemini Live Agent Challenge hackathon ($80,000 prize pool, 7,500+ participants, UI Navigators category). The goal is to produce an engaging 3-minute overview that hits every judging criterion while telling a compelling story. The tone should be enthusiastic but grounded in real technical achievement, not hype.

---

## THE PROBLEM (30 seconds)

2.2 billion people worldwide have some form of visual impairment according to the World Health Organization. The web is built for eyes: finding an apartment on Zillow, shopping on Amazon, or reading news on CNN requires scanning layouts, clicking buttons, and interpreting visual context that screen readers simply cannot handle well. Modern single-page applications with dynamic JavaScript layouts break traditional DOM-based screen readers about 20-30% of the time. The fundamental problem is that most assistive tools try to read the source code of a webpage rather than looking at what is actually on screen.

## THE BREAKTHROUGH IDEA (20 seconds)

AccessBrowse takes a radically different approach: instead of parsing the DOM or relying on ARIA tags, it looks at websites the same way a sighted person does, visually, using Gemini Computer Use. Combined with Gemini Live API for real-time voice conversation, users can browse any website by simply talking. "Find me apartments in Seattle under $1000 on Zillow." No keyboard shortcuts. No tab navigation. No understanding of page structure required. Just speak, and browse.

## HOW IT WORKS: THE MULTIMODAL UX LOOP (30 seconds)

AccessBrowse is a Chrome extension paired with a Python FastAPI backend running on Google Cloud Run. The experience is a continuous multimodal loop:

1. The user speaks a request through their microphone
2. Audio streams in real-time over WebSocket to the backend
3. Gemini Live API (gemini-2.5-flash-native-audio) understands the intent through bidirectional voice streaming
4. When browsing is needed, Gemini calls the browse_web tool which triggers a multi-step action loop
5. The extension captures a screenshot of the current page
6. Gemini Computer Use (gemini-2.5-computer-use) analyzes the screenshot and returns precise coordinates for the next action on a normalized 1000x1000 grid
7. The content script translates coordinates to viewport pixels using document.elementFromPoint and executes the action: click, type, scroll, hover, drag, or any of 13 supported action types
8. Steps 5 through 7 repeat until the task is complete (up to 10 steps per browse action)
9. Gemini speaks the results back to the user at 24kHz audio quality, which is noticeably clearer than the standard 16kHz

This works on ANY website with zero configuration. No CSS selectors. No DOM parsing. No site-specific setup. It is coordinate-based visual browsing, which is the key innovation.

## LIVE DEMO SCENARIOS (60 seconds)

The accompanying screenshots show AccessBrowse in action across six different real websites, demonstrating versatility:

Screenshot 1 - Amazon Product Search: The user says "Find me noise-canceling headphones on Amazon." AccessBrowse navigates to Amazon, types the query in the search box, and reads back results including prices and ratings. The sidepanel shows the full conversation transcript with step-by-step status updates.

Screenshot 2 - CNN News Headlines: The user says "Read me today's top headlines on CNN." AccessBrowse navigates to CNN and uses the read_page tool to generate an accessibility-focused summary of the page, then reads the headlines aloud including gas prices, international news, and trending stories.

Screenshot 3 - Redfin Home Search: The user says "Search for homes in Seattle on Redfin." AccessBrowse finds 2,002 homes for sale and describes the top listings with prices, bed/bath counts, and neighborhood details.

Screenshot 4 - Zillow Apartment Rental Search: The user says "Find apartments in Seattle under $1000 on Zillow." This demonstrates the system working on complex map-based interfaces with filters, finding 12,371 rentals and summarizing the best options.

Screenshot 5 - Google Restaurant Search: The user says "Search for the best restaurants near me." AccessBrowse returns rated results with reviews, demonstrating that it handles Google's rich search results layout.

Screenshot 6 - Wikipedia Article Reading: The user says "Read the Wikipedia article on web accessibility." This is thematically perfect, demonstrating AccessBrowse reading an article about the very problem it solves.

Every single one of these scenarios works because of coordinate-based browsing. No site-specific code. No CSS selectors. The same system handles Amazon, Zillow, CNN, Redfin, Google, and Wikipedia identically.

## KEY TECHNICAL WINS THAT SHOULD IMPRESS JUDGES (40 seconds)

Win 1 - Coordinate-based browsing works on ANY website: Unlike DOM-scraping or selector-based approaches that break on 20-30% of modern websites, Gemini Computer Use analyzes screenshots visually. The normalized 1000x1000 coordinate grid abstracts away viewport size entirely. This is the UI Navigator category's key criterion: "visual precision and understanding screen context rather than blind clicking."

Win 2 - True real-time bidirectional voice: This is not a turn-based chatbot. Gemini Live API provides continuous bidirectional audio streaming at 16kHz input and 24kHz output. The user can interrupt (barge-in) at any time. Filler speech like "Let me look that up..." provides immediate feedback before tool execution begins.

Win 3 - Production-grade engineering, not a prototype: 149 automated tests (107 Python across 7 suites plus 38 JavaScript content script tests plus 4 end-to-end tests). GitHub Actions CI pipeline. Infrastructure-as-Code deployment with deploy.sh. Dockerized backend. Maximum 3 concurrent sessions with idle timeout cleanup. This is production-ready software.

Win 4 - Deep integration with Google Cloud Platform: Cloud Run for serverless container hosting. Vertex AI for model access. Gemini Live API for real-time voice. Gemini Computer Use for visual understanding. The entire inference pipeline runs on GCP.

Win 5 - 13 action types for complete web interaction: click, type, scroll, hover, key press, drag, select, go back, go forward, navigate, wait, read page, and done. This covers the full range of web interaction, not just clicking links.

Win 6 - Fully async architecture: Every component runs on async event loops with zero blocking operations. A single Cloud Run instance handles 3 concurrent voice browsing sessions simultaneously. asyncio.Event objects coordinate screenshot relay and action results across the WebSocket, Gemini API, and extension message channels.

## IMPACT AND MARKET (20 seconds)

2.2 billion people with visual impairment. Web Content Accessibility Guidelines (WCAG) compliance remains poor across the internet, with studies showing 96.3% of home pages have detectable WCAG 2 failures. AccessBrowse does not wait for websites to become accessible. It makes them accessible right now, today, by looking at them visually. This is assistive technology that works with the web as it actually exists, not as standards committees wish it existed.

The technology also applies beyond visual impairment: motor disabilities, cognitive disabilities, elderly users who find complex UIs confusing, and even hands-free operation scenarios like cooking or driving.

## TECHNOLOGY STACK

- Backend: Python 3.12, FastAPI, Google GenAI SDK
- AI Models: Gemini Live API (gemini-2.5-flash-native-audio), Gemini Computer Use (gemini-2.5-computer-use)
- Cloud: Google Cloud Run, Vertex AI
- Extension: Chrome MV3, TypeScript, React 18, Web Audio API
- Infrastructure: Docker, deploy.sh (Infrastructure as Code), GitHub Actions CI
- Tests: 149 total (107 Python pytest + 38 JavaScript + 4 E2E)

## JUDGING CRITERIA MAPPING

| Criterion | Score | How AccessBrowse Addresses It |
|-----------|-------|-------------------------------|
| Creativity & Innovation | 2.0 | Coordinate-based visual browsing is a fundamentally new approach to web accessibility. No DOM parsing, no selectors, just vision. |
| Usefulness | 2.0 | Addresses a real problem for 2.2B people. Works on real websites like Amazon, Zillow, and CNN today. |
| Technical Execution | 2.0 | 149 tests, CI pipeline, fully async architecture, 13 action types, production-ready code. |
| Use of GCP | 2.0 | Cloud Run + Vertex AI + Gemini Live API + Gemini Computer Use. The entire pipeline is GCP-native. |
| Presentation | 2.0 | 6 real-website demo screenshots, architecture diagram, polished README, comprehensive documentation. |
| Blog Post Bonus | +0.6 | Published blog post with #GeminiLiveAgentChallenge. |
| IaC Bonus | +0.2 | deploy.sh in public GitHub repository. |
| GDG Bonus | +0.2 | Google Developer Group membership. |
| Maximum Possible | 11.0 | All bonus categories addressed. |

## CLOSING STATEMENT

AccessBrowse transforms web browsing from a visual experience into a conversational one. Powered by Gemini Live API for real-time voice and Gemini Computer Use for visual understanding, deployed on Google Cloud Run, it makes any website accessible through natural conversation. 13 action types. Any website. Zero configuration. Making the web accessible, one conversation at a time.

---

## NOTEBOOKLM GENERATION INSTRUCTIONS

When generating audio from this document, please create an engaging, conversational overview in the style of a tech product demo or a short podcast episode. The tone should be:

- Enthusiastic but technically credible (not salesy or overhyped)
- Focused on the "wow factor" moments: coordinate-based browsing on any website, 2.2 billion affected users, 149 automated tests, real-time bidirectional voice
- Structured as: Problem (why this matters) -> Solution (what AccessBrowse does) -> Demo walkthrough (reference the screenshots) -> Technical depth (impress the judges) -> Impact (why this wins)
- Approximately 3 minutes in length
- Include specific numbers: 2.2 billion users, 13 action types, 149 tests, 24kHz audio, 6 demo websites, $80K prize pool, 7,500 participants

The screenshots provided alongside this document show the real AccessBrowse sidepanel UI overlaid on live websites (Amazon, CNN, Redfin, Zillow, Google, Wikipedia) with realistic voice transcripts demonstrating the conversation flow.
