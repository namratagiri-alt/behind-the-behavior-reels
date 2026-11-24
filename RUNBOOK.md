# Behind the Behavior: production and publishing runbook

This is the operating manual for every scheduled run. The master editorial brief is the project doc "AUTONOMOUS PSYCHOLOGY REELS CONTENT STUDIO". Its rules on scientific accuracy, ethics and storytelling override anything here.

## Fixed locations

| Item | Location |
|---|---|
| Drive root | "Psychology Reels Studio" folder, id 1ROYeqQaeVbXT97IycGYPsRvj0d6Azd1i |
| Engine (reelengine.py, qc.py, this runbook) | Drive folder 01_engine, id 1Z5C3oBCOYYLZPiudS-KqLPgZDojZLxlI |
| Reel specs (Rxxx.json) | Drive folder 02_reel_specs, id 1yoBQSYHdygf8xwj6qWomO9XO4eTlEqxe |
| Covers, captions package | Drive folder 03_ready_to_publish, id 14cfvempIeDJlL5aZ3pCReg0fyWB3zWgO |
| Editorial tracker (Google Sheet) | id 12AAlCmHdQ8k2gpLwfmdteWtz2AsyOs_MR1q_Q_gkMos |
| Video hosting | GitHub repo namratagiri-alt/behind-the-behavior-reels, folder media/. Public URL pattern: https://cdn.jsdelivr.net/gh/namratagiri-alt/behind-the-behavior-reels@main/media/<ID>.mp4 (served as video/mp4). Fallback: https://raw.githubusercontent.com/namratagiri-alt/behind-the-behavior-reels/main/media/<ID>.mp4 |
| Instagram publishing | Windsor.ai connector "instagram", action create_video_post, account purpllewave (17841476377023976). Never publish to nammyfit14 (17841402171283573). |

Drive uploads are limited to about 3 MB per file through the connector, so MP4s never go to Drive. They go to GitHub.

## Environment setup (each run starts fresh)

1. pip install --break-system-packages -q kokoro-onnx soundfile numpy pillow
2. Download the voice model (Apache 2.0) from GitHub releases into /home/claude/models:
   - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
   - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
3. Get reelengine.py and qc.py: prefer the copies in the GitHub repo (engine/); otherwise download from Drive folder 01_engine. Write them to /home/claude/studio/engine/.
4. Attach the GitHub repo with push access (add_repo owner namratagiri-alt, repo behind-the-behavior-reels, access push) and clone it.

## Making a Reel

1. Pick the next tracker row whose status is "Concept" (or the row for today's planned date). Skip rows with a score below 32 or flagged "needs evidence review" unless the evidence review is done in this run.
2. Research: verify every claim with primary or authoritative sources via web search. Record each claim, evidence strength and source URL. Drop or soften claims you cannot verify. Never invent studies, numbers or quotes.
3. Write three hooks, choose one, then write the spec JSON (same schema as R001.json). Length is 30 to 45 seconds, chosen by topic (simple ideas nearer 30, intersections nearer 45). Every scene carries a "role", in this order, and qc.py enforces the timing:
   - hook (0 to 3 s): one headline or question scene, 6 to 9 spoken words, with the same idea as on-screen text. The engine shows hook text from the first frames and starts the voice at 0.15 s.
   - setup (3 to about 15 s): one or two scenes that give the core point or situation the viewer recognizes.
   - proof (about 15 to 25 s, may run longer in a 40+ s Reel): evidence, a concrete example, or a clear visual change (new scene type, comparison, chain, countdown).
   - takeaway (last 5 to 8 s): one question scene that lands the insight or loops back to the hook. The engine pads it to at least 5.6 s on screen.
   Typical total: 75 to 100 spoken words at speed 1.05 to 1.12. If QC fails a timing check, add or cut words in the setup or proof scenes rather than changing the hook or takeaway. Scene types available: headline, compare, axis, bars, countdown, stack, chain, split, chat, question. Bars are always labeled illustrative by the engine. brand = "Behind the Behavior", voice af_heart.
4. Render: python3 -I engine/reelengine.py reels/<ID>.json out/<ID>
5. QC: python3 -I engine/qc.py out/<ID> <ID>. auto_pass must be true. Then open out/<ID>/<ID>_contact.png with Read and check: text fits, nothing overlaps, no text in the bottom 430 px except subtitles, visuals match the narration, no misleading statement. Fix the spec and re-render until clean.
6. Caption: insight that adds to the voiceover, one question, a short source line, "Voiceover is AI-generated.", 3 to 5 specific hashtags. No em dashes. Plain American English.
7. Save: commit media/<ID>.mp4 and media/<ID>_cover.jpg and specs/<ID>.json to the repo and push. Upload <ID>.json to Drive 02_reel_specs and <ID>_cover.jpg to Drive 03_ready_to_publish.

## Publishing

1. Idempotency: if the tracker row already shows a media ID, or the account's recent media already contains this Reel's caption opening, do not publish again.
2. Confirm the public video URL returns HTTP 200 with a video content type before calling Windsor.
3. Windsor execute_action, connector instagram, account = the Behind the Behavior account, action create_video_post, params: video_url, caption, cover_url (jsDelivr URL of the cover JPEG), share_to_feed true.
4. Only mark "Published" when Windsor returns a media ID. Record media ID, permalink if available, and published time in the tracker. On failure, record the error, retry once, then mark "Publish failed" and notify.

## Escalate instead of publishing

Sensitive topics (mental health, trauma, child safety, diagnosis), evidence you could not verify, account access problems, unexpected charges, or anything that would change the brand. Produce the assets, hold publishing, and notify.

## Tracker updates

The Drive connector cannot edit individual sheet cells. Read the sheet, change the rows in a local CSV, and upload the full CSV as a new Google Sheet revision only if a content-update tool is available; otherwise keep an append-only log file "publish_log.csv" in the GitHub repo and report status in the run notification.
