# Behind the Behavior: production and publishing runbook

This is the operating manual for every scheduled run. The master editorial brief is Namrata's project doc "AUTONOMOUS PSYCHOLOGY REELS CONTENT STUDIO"; its essentials are consolidated below in "Master brief essentials", so runs do not depend on being able to open that doc. Its rules on scientific accuracy, ethics and storytelling override anything else here.

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

## Source guide (added 25 Nov 2026 from Namrata's suggestions)

Use these to find ideas, then verify every claim at the level shown. A Reel's core claim must rest on Tier 1 or 2. Never quote or closely paraphrase book passages; explain ideas in your own words and credit the author.

| Source | Tier | How to use it |
|---|---|---|
| Nature Human Behaviour (and similar peer-reviewed journals) | 1, primary | Cite directly. Check sample, effect size, and whether it is one study or a meta-analysis. Prefer recent, preregistered or replicated work. |
| Thinking, Fast and Slow (Kahneman, 2011) | 2, expert synthesis | Great idea source for biases and heuristics. Cite the underlying studies, not just the book. Avoid the behavioral priming material in chapter 4 and treat ego depletion as contested: both had replication failures, which Kahneman himself acknowledged. |
| The Psychology of Money (Housel, 2020) | 3, popular essays | Idea source for money behavior (reasonable vs rational, compounding, getting wealthy vs staying wealthy). Its stories are illustrations, not evidence. Find research on the mechanism (mental accounting, hedonic adaptation, social comparison) before making a claim. |
| Everyday Psychology (Gopal Rayappa Kolekar); Everyday Psychology: Applying Psychological Insights in Modern Life | 3, general books | Idea source for relatable scenarios. Verify every mechanism in primary research. |
| Psychology Today (psychologytoday.com) | 3, expert blogs of mixed quality | Use for leads. Follow each post's citations to the original study; do not cite the blog as proof. |
| PositivePsychology.com | 3, secondary summaries | Use for leads and reading lists; cite the primary studies it links. |
| Marriage Foundation (marriagefoundation.org.uk) | 3, advocacy charity | It argues for marriage, so treat its framing as a position. Use for questions and leads only; check claims against peer-reviewed research, and say "linked to" rather than "causes" because most relationship data are correlational. |
| Emotiv workplace psychology glossary | 4, vendor glossary | Definitions and topic ideas only. Never cite as evidence. |

Relationship and marriage topics: avoid implying one family structure is better for everyone, avoid blaming partners, and do not diagnose. Money topics: explain behavior, never give investment advice.

## Research themes (added 25 Nov 2026 from Namrata)

Prioritize these when choosing or researching concepts. The notes say where the evidence is strong and where to be careful. Always verify current sources before publishing.

1. Money stress and relationships (financial conflict, secrecy, income differences, money values vs relationship satisfaction). Evidence: mostly correlational survey and longitudinal work (for example Dew, Britt & Huston 2012 on financial disagreements and divorce); some field experiments on joint finances. Say "linked to", never "causes". No blame on either partner.
2. Behavioral savings interventions (automatic transfers, defaults, reminders, commitment devices, progress tracking). Evidence: strong for defaults and automatic enrollment (Madrian & Shea 2001), commitment and escalation designs (Thaler & Benartzi 2004; Ashraf, Karlan & Yin 2006), reminders (Karlan et al. 2016). Note most evidence is retirement or developing-country savings; be precise when talking about emergency savings.
3. Cognitive biases in money and career decisions (loss aversion, present bias, anchoring, confirmation bias). Evidence: anchoring and present bias are well supported. Loss aversion is real but its size and scope are debated (for example Gal & Rucker 2018); avoid "losses hurt twice as much" as a universal law.
4. Habit formation for financial health (small automated habits vs willpower budgeting). Evidence: automation and defaults beat active choice in many studies; habit formation takes highly variable time (Lally et al. 2010: median 66 days, range 18 to 254). Direct head-to-head tests against willpower budgeting are limited, so frame as "evidence suggests", not "proven".
5. Psychological safety and performance (trust, feedback culture, leader behavior). Evidence: Edmondson 1999 and the Frazier et al. 2017 meta-analysis. Google's Project Aristotle is a company report, not peer-reviewed; cite it only as an example.
6. Workplace bias and fair evaluation (heuristics and implicit bias in hiring, appraisal, promotion). Evidence: strong field experiments on hiring discrimination (Bertrand & Mullainathan 2004), halo and recency effects in appraisal. The implicit association test predicts individual behavior weakly (Oswald et al. 2013; Forscher et al. 2019): do not claim an IAT score shows how a person will act. The blind-orchestra study (Goldin & Rouse 2000) has published statistical critiques; mention carefully or avoid.
7. Well-being beyond income (PERMA: positive emotion, engagement, relationships, meaning, accomplishment; Seligman 2011; Butler & Kern 2016 PERMA-Profiler). Do not say income does not matter: recent work finds well-being keeps rising with income on average (Killingsworth 2021; Killingsworth, Kahneman & Mellers 2023). Frame as "income matters, and these matter too", unless a specific study directly compares them.
8. Marital conflict repair (communication and repair behaviors in couples who stay satisfied vs dissolve). Evidence: Gottman's longitudinal lab studies (for example Gottman & Levenson 2000) and repair-attempt research. Avoid the widely repeated "predicts divorce with 90%+ accuracy" figure: it came from fitting the model to the same sample and has been criticized. Never diagnose a relationship.

## Source guide, part 2 (added 25 Nov 2026 from Namrata)

Same rule: a Reel's core claim rests on Tier 1 or 2. Books give ideas and framing; cite the studies behind them. No quoting or close paraphrase of book text.

### Relationships and marriage
| Source | Tier | Use and cautions |
|---|---|---|
| Gottman & Krokoff 1989, Marital interaction and satisfaction: a longitudinal view (J Consulting and Clinical Psychology) | 1 | Primary. Note its nuance: some conflict engagement predicted better long-term satisfaction, so "fighting is bad" is the wrong takeaway. |
| Gottman & Levenson 1992, Marital processes predictive of later dissolution (JPSP) | 1 | Primary. Report findings as associations; avoid divorce-prediction accuracy figures. |
| APA, "Lessons from the Love Lab"; APA, "Can this marriage be saved?" | 2 | Expert summaries; follow to primary studies for any specific number. |
| The Seven Principles for Making Marriage Work (Gottman & Silver) | 2-3 | Practical framing of Gottman's research; cite the underlying studies. |
| The Gottman Institute research pages | 3 | Accessible overview, but the institute sells programs. Leads only. |
| Hold Me Tight (Sue Johnson) | 3 | Emotionally Focused Therapy has controlled-trial support (verify current meta-analyses); the book is a practitioner perspective. Do not present it as therapy advice. |
| Attached (Levine & Heller) | 3 | Attachment theory is well established (Bowlby; Hazan & Shaver 1987), but the book simplifies it. Never label viewers or partners as an attachment "type". |

### Habits, motivation and well-being
| Source | Tier | Use and cautions |
|---|---|---|
| Wood & Runger 2016, Psychology of habit (Annual Review of Psychology) | 1 | Strong review; preferred habit source. |
| Lally et al. 2010 (European Journal of Social Psychology) | 1 | Median 66 days, range 18 to 254; small sample, self-reported automaticity. |
| Mertens et al. 2022, The effectiveness of nudging (PNAS) | 1, with caution | Published replies argued that after correcting for publication bias the average effect may be much smaller or near zero (for example Maier et al. 2022, PNAS). Do not cite its average effect size as settled; cite specific well-replicated nudges (defaults) instead. |
| Seligman 2018, PERMA and the building blocks of well-being (J Positive Psychology); Penn Positive Psychology Center scholarly articles | 2 | Framework and curated readings. PERMA is a framework, not proof that its parts cause well-being. |
| Mindset (Carol Dweck) | 2-3 | Growth-mindset interventions show small average effects, larger for some groups (Sisk et al. 2018 meta-analyses; Yeager et al. 2019, Nature). Avoid "mindset transforms results". |
| Drive (Daniel Pink) | 3 | Popular take on self-determination theory; cite Deci & Ryan. Rewards do not always undermine motivation; be precise. |
| Atomic Habits (James Clear); The Power of Habit (Charles Duhigg) | 3 | Practical frameworks. The 21-day myth and some anecdotes are not evidence; back mechanisms with Wood & Runger or Lally. |

### Money and decision-making
| Source | Tier | Use and cautions |
|---|---|---|
| Kahneman & Tversky 1979, Prospect theory (Econometrica); Tversky & Kahneman 1974, Judgment under uncertainty (Science) | 1 | Foundational. Loss-aversion size is debated; anchoring is robust. |
| CFPB: Financial well-being (goal of financial education); Evidence-based strategies to build emergency savings; behavioral economics research portal | 1-2 | Strong institutional research, US-specific. Check that pages are still available and current before citing; label findings as US data when the audience is broader. |
| Nudge (Thaler & Sunstein) | 2-3 | Framework; cite underlying studies (for example Madrian & Shea 2001). |
| Scarcity (Mullainathan & Shafir) | 2-3 | Some headline lab findings have had mixed replication results; verify the specific study before using it. |
| The Psychology of Money (Housel); Thinking, Fast and Slow (Kahneman) | see part 1 | See part 1 cautions. |

### Workplace and organizational psychology
| Source | Tier | Use and cautions |
|---|---|---|
| Industrial and Organizational Psychology (journal) | 1 | Peer-reviewed; many articles are focal-article-plus-commentary debates, so note when a piece is a position paper. |
| SIOP "Primary Sources" readings | 1 | Curated primary research; good starting point. |
| SIOP Guidelines for Education and Training in I-O Psychology; APA employer resources | 2 | Topic maps and applied summaries; follow to primary research for claims. |
| The Fearless Organization (Amy Edmondson) | 2 | Written by the researcher; cite Edmondson 1999 and later studies. |
| Thinking, Fast and Slow | 2 | Strong for hiring and evaluation judgment (structured vs intuitive judgment); see part 1 cautions. |
| Dare to Lead (Brene Brown) | 3 | Based on qualitative research; inspirational framing. Use for themes, not causal claims. |
| Drive (Daniel Pink) | 3 | See above. |

## Content system v2 (added 25 Nov 2026 from Namrata; supersedes earlier pillar and structure notes)

### Five content pillars (every Reel belongs to one; rotate them)
| Pillar | Core question | Example topics |
|---|---|---|
| Habits and behaviour | Why do we repeat actions? | habit loops, environment design, procrastination, dopamine myths |
| Thinking and decisions | Why do we choose poorly? | confirmation bias, loss aversion, sunk cost, overthinking |
| Perception and attention | Why do we see situations differently? | selective attention, framing, illusions, first impressions |
| Social influence | Why do we conform or persuade? | social proof, conformity, authority, groupthink, persuasion |
| Emotions and relationships | Why do we react this way? | emotion regulation, attachment, conflict, boundaries, empathy |
Money, work, parenting and relationships are contexts inside these pillars (tracker column "Context"), not separate pillars.

### Structure: explain, example, apply (enforced by qc.py)
- Hook, 0 to 2 s: a specific problem, surprising claim, number or visual change, 5 to 7 spoken words, same idea as on-screen text. No intros.
- Explain, about 2 to 15 s: the mechanism in plain language.
- Example, about 15 to 25 s: one everyday situation; use Indian and global everyday scenarios (salary credit day, family WhatsApp group, festival sales, office meetings, commutes, exams).
- Apply, last 5 to 8 s: one small, realistic action plus one engagement prompt ("Save this for your next salary day"). The engine adds the fixed sign-off "Understand the pattern. Change the response." to the closing scene.
- Total 30 to 45 s by topic (QC limit) unless Namrata changes it.
- Spec roles stay hook / setup / proof / takeaway (setup = explain, proof = example or evidence, takeaway = apply).

### Language and credibility
- Careful wording: "research suggests", "one explanation is", "it may help". Never "this proves", "everyone does this", "this will fix your life".
- Cite briefly on screen when a number is shown (bars "source" field) and always in the caption (author, year, journal).
- Debunk myths with evidence (series "Myth vs reality"). Never diagnose, never present pop-psychology labels as fact.

### Shareability (Instagram says its most important Reels predictions are reshare, full watch-through and like)
- Every Reel needs a clear reason to send or save it, stated in the closing kicker or caption.
- One focused question in the caption.
- Subtitles always on (engine does this).

### Format risk to manage
Instagram says it may show fewer Reels that are "majority text", low-resolution or watermarked. Our Reels mix animated text, diagrams and illustrated scenes (no watermark). Until Namrata decides otherwise: keep on-screen words short (headline lines of 2 to 4 words where possible), prefer diagram, chart, chat, split and countdown scenes over plain headline scenes (no more than 2 headline scenes per Reel), and watch reach per Reel in the weekly review.

### Master tracker (always at least 30 ideas)
- tracker.csv in this repo is the master. Columns include status, pillar, context, hook, action, score, evidence anchors and cautions, slot, published time, media id, metrics (views, reach, average watch time, shares, saves, comments, profile visits, follows), insights and "Namrata notes".
- Statuses: Idea, Idea (needs evidence review), In production, Published, Held, Skipped (with reason in Insights).
- Every production run updates its row. The weekly run fills metrics and insights and tops the queue back up to at least 30 eligible ideas (score 32+, evidence 3+), balanced across the five pillars.
- After updating tracker.csv, refresh the Google Sheet mirror "Behind the Behavior content tracker" in Drive folder 1ROYeqQaeVbXT97IycGYPsRvj0d6Azd1i: first read the current mirror and copy any text Namrata added in the "Namrata notes" column into tracker.csv, then upload tracker.csv as a new Google Sheet with the same name and trash the previous mirror.

## Hook bank and curiosity series (added 25 Nov 2026)
- hooks/ holds Namrata's hook banks: career_and_workplace.txt, relationships.txt, curiosity_series.txt, plus hook formulas. Read hooks/README.md first.
- Recurring curiosity series you may use as the "Series" label: Do you know why?; Have you wondered?; Are you aware?; The psychology behind...; Your brain is not broken; One small shift; Myth vs psychology. Keep series names stable so viewers recognize them.
- Relationship Reels formula: name the feeling or pattern (hook), reframe with the psychology in one sentence, realistic example, one small respectful step, CTA such as "Save this for your next difficult conversation."

## Sensitive topics (added 25 Nov 2026)
Autonomous runs may cover these only as described; otherwise set status "Held" and notify Namrata.
- Burnout and stress: allowed as everyday workplace psychology (job demands, recovery, role ambiguity) with no diagnosis and no clinical claims. If a Reel would discuss depression, anxiety disorders, panic, self-harm or medical symptoms, hold it.
- Body image, eating, restriction, food guilt, weight: always hold for Namrata's review. These can harm vulnerable viewers, including teens.
- Relationships: never diagnose. If a Reel touches control, coercion, abuse or feeling unsafe, add on screen and in the caption that professional or specialist support matters when there is abuse or a safety concern, and hold for review the first time this framing is used.
- Career and money: explain psychology and evidence; never give individual financial, legal or HR advice; add "Not financial advice" where pay or money decisions are discussed.
- Contested findings to avoid stating as fact: "mental effort drains willpower" (ego depletion), "people leave managers, not companies" as a universal rule, "Sunday scaries" or "silence wins negotiations" as research findings, and attachment "types" as fixed labels.

## Illustrated scenes and watermark (added 25 Nov 2026)
- Every Reel scene can carry an "illustration" key. Available: desk, phone, shelf, meeting, night, kitchen, commute, park, money, calendar (engine/illustrations.py; faceless flat illustrations drawn in code, no people, no faces, no text). The engine drifts them slowly behind the content with a dark scrim so text stays readable.
- qc.py requires at least half the scenes to be illustrated and no more than 2 headline scenes. Pick illustrations that match the everyday example (salary/saving: money or calendar; work: desk or meeting; texting: phone; home: kitchen; late-night thoughts: night; travel: commute; children: park; shopping: shelf).
- Do not use Canva or Figma image generation from automated runs: Canva credits are exhausted and Figma runs on the Inovaare company plan. If more illustration types are needed, add them to illustrations.py in the same style.
- Watermark is OFF by default (spec "watermark": false or omitted). Instagram says it may show fewer watermarked or majority-text Reels.

## Weekly carousel (added 25 Nov 2026)
- One carousel a week, posted by the "Behind the Behavior weekly carousel" scheduled task (Saturdays 12:53 PM IST).
- Format: engine/carousel.py renders 1080x1350 JPEG slides: cover, 5 to 8 item slides (title, plain explanation, "Try:" action, short source), closing slide (one action, save prompt, sign-off). Carousel specs live in carousels/Cxxx.json; images in media/carousels/.
- Good carousel topics: checklists and frameworks ("7 thinking traps", "5 habit design rules", "Myth vs psychology: 6 claims"), each item backed by a Tier 1 or 2 source. Carousels may be text-led; the majority-text concern applies to Reels.
- Publish with Windsor execute_action, connector instagram, account 17841476377023976, action "create_carousel_post", params image_urls (2 to 10 commit-pinned jsDelivr URLs, JPEG under 8 MB, 4:5) and caption. Log to publish_log.csv with slot "CAROUSEL" and add a tracker row with the carousel ID.

## Hosting size rule (jsDelivr 50 MB limit)
jsDelivr refuses new files (HTTP 403, "Package size exceeded the configured limit of 50 MB") once the repo tree at a commit passes 50 MB. Instagram keeps its own copy after publishing, so:
- In the commit that adds a new media/<ID>.mp4, `git rm` every other media/*.mp4 whose Reel is already published (they stay recoverable in git history). Never remove an MP4 that is not yet published.
- Before pushing, check `du -sh --exclude=.git .` is under 40 MB. If carousel JPEGs or covers push it near that, prune published ones the same way.
- Always confirm each jsDelivr URL returns 200 with the right content type before publishing. If jsDelivr still fails, raw.githubusercontent.com commit-pinned URLs work for JPEGs (used for C001 on 25 Nov). They serve MP4s as application/octet-stream, which is untested with Instagram, so for video, fix the size and use jsDelivr.


## Account handle
On 25 Nov 2026 the Instagram handle changed from @purpllewave to @whats.behind.the.behavior. Same account, Windsor.ai id 17841476377023976. The rename invalidated Windsor's session; it was reconnected via the Facebook Login link the same day. A future rename or password change will do the same: reconnect via Windsor's Facebook Login link (replace_instagram_login=17841476377023976).


## Master brief essentials (consolidated 25 Nov 2026 from "AUTONOMOUS PSYCHOLOGY REELS CONTENT STUDIO")
Read this before choosing or writing any Reel or carousel. It overrides other sections where they conflict, except Namrata's later explicit decisions (30 to 45 s length, two Reels a day, five pillars, sign-off, watermark off).

### Positioning: the differentiator
- Central proposition: the invisible psychology behind everyday life. The viewer should think "I've experienced this, but I never understood why it happens."
- The central creative question for every piece: what invisible psychological process is operating here, and how do we make the viewer recognize it in their own life?
- Brand personality: intelligent, observant, surprising, accessible, occasionally provocative. Like a behavioral science publication turned into short visual stories. No motivational cliches, simplistic life advice, exaggerated self-help claims or recycled psychology trivia.
- Psychological intersections are the main differentiator. Explore both single mechanisms and two or more mechanisms that interact (reinforce, contradict or moderate each other), for example: sale purchase = anchoring + transaction utility + anticipated regret; checking work messages at night = variable reinforcement + workplace norms + anticipated consequences; defending a poor decision = cognitive dissonance + sunk cost + self-image protection. Never force several concepts in; scientific coherence beats complexity. Aim for most Reels in a week to carry a genuine intersection.
- For each topic answer: what observable behavior are we explaining; which principle is most relevant; is a second one needed; do they reinforce, contradict or moderate; what research supports it; what alternative explanations exist; what makes it surprising, practical or discussion-worthy.

### Territories inside the five pillars
Use these as the "Context" column and to keep variety: social, behavioral, cognitive, consumer, retail, workplace, leadership, employee, parenting, child and adolescent, relationship, family and household (invisible labor, mental load, decision fatigue), money, digital (notifications, comparison, online identity), emotional (guilt, shame, regret, jealousy, anticipation), everyday decisions (procrastination, choice overload, self-justification). Examples should span life stages and roles without stereotyping by gender, occupation, family structure or age.

### Topic selection
- Prioritize: everyday relevance, a surprising or counterintuitive explanation, a recognizable real-life scenario, credible evidence, visual storytelling potential, and a reason to save, share or discuss.
- Reject generic or famous-term-definition topics. Weak: "5 signs you are intelligent", "3 types of toxic people", "Psychology says never trust these people", "7 tricks to make anyone like you". Strong: "Why competent people underestimate how much others know", "Why praise can make someone more anxious about their next performance", "Why neutral messages feel negative when we are uncertain", "Why we mistake familiarity for quality", "Why a child can understand a rule but not follow it when overwhelmed".
- Originality check before approving: fresh example, real intersection, overlooked consequence or stronger explanation than common content. Never copy another creator's scripts, storytelling or visuals.
- Do not publish consecutive pieces about essentially the same bias.

### Storytelling formats (record in the tracker "Format" column; never 5 in a row with the same formula)
A The Invisible Reason (familiar action, then the hidden psychology). B Two Psychological Forces (competing or reinforcing mechanisms; a metaphor, not a brain-region claim). C One Situation, Two Reactions (same event, different interpretation). D Psychology in Action (viewer recognizes the behavior before the concept is named). E The Psychology of a Decision (reconstruct the mental steps). F Counterintuitive Psychology (challenge an assumption with evidence, no absolute claims). G The Psychological Chain Reaction (one response triggers the next; the chain scene fits). H The Human Behavior Case Study (clearly fictional or clearly documented, never blurred). I Psychology You Can Use (practical, not a universal fix). J The Hidden Social Rule (unwritten norms in families, work, shopping, friendships).
Engine scene hints: B and C use split or compare; G uses chain; E uses chain or axis; D uses chat; F uses bars with a source.

### Script quality rules
- Write three hooks; pick the clearest, most relevant, most original. The hook must be something the script fully delivers; no clickbait.
- Recognition before terminology: show the situation before naming the concept. Do not spend half the Reel defining terms.
- Each sentence must advance the explanation; one central narrative thread; concrete behavior over abstractions; tension between expectation and reality where useful; no padding to reach a length.
- Endings: one natural ending (thoughtful question, useful takeaway, surprising observation, reason to save, new perspective). No robotic or repetitive engagement bait.
- Recurring series names from the brief, usable as the "Series" label alongside the curiosity series: The Psychology Behind It; Two Forces, One Decision; Why We Do That; The Psychology of Buying; What Your Workplace Is Teaching You; Inside the Parent-Child Dynamic; The Invisible Rules of Human Behavior; Your Brain at Work; The Decision You Didn't Notice Making.

### Creative score (tracker "Score /40")
Score 1 to 5 on each: Curiosity, Recognition, Psychological depth, Evidence, Originality, Storytelling, Shareability, Visual potential. Equal weights, maximum 40. Produce only 32+ with Evidence 3 or more. It is a working editorial rule, not a predictor of virality.

### Scientific credibility (non-negotiable)
- Identify the core claim; find primary research, systematic reviews or reputable academic sources; separate well-supported findings from emerging, contested or popular interpretations; check the finding generalizes to the scenario; note caveats and competing explanations; verify every number, named study and quote.
- Keep a source log for every Reel: record sources with URLs and what each supports in the tracker "Evidence anchors" column (and "Evidence cautions" for caveats).
- Never invent studies, statistics, neuroscience, quotes or terms. Never label people as narcissists, sociopaths, psychopaths or mentally ill. Never diagnose from an ordinary behavior. Never imply one universal cause. If evidence is limited, qualify or choose a stronger topic.

### Ethical guardrails
- Never present manipulation, coercive control or exploitation as desirable. Sales, pricing and persuasion content explains how mechanisms work; it never teaches deceptive targeting of vulnerable people.
- Parenting and children: no blaming or shaming parents or children; no diagnoses from isolated behavior; acknowledge developmental and contextual variation; protect children's privacy; never portray real children as having conditions.
- Workplace: distinguish individual behavior from organizational conditions; do not stereotype managers or employees; never frame unethical management tactics as acceptable.
- Relationships and social: no universal gender differences; theories are not mind-reading tools; separate hypotheses about behavior from verified motives.
- All: no plagiarism, no unlicensed audio or images, follow AI-content labeling ("Voiceover is AI-generated."), never promise clinical, psychological or financial outcomes.

### Starter concept list from the brief (validate before use; generate stronger alternatives when needed)
50% discount spending (anchoring, transaction value, anticipated regret); guilt about free time (internalized norms, self-worth, productivity expectations); a manager's silence feeling worse than criticism (ambiguity, threat appraisal); trusting expensive products more (price-quality inference, signaling); refreshing an app expecting nothing (checking routines, unpredictable rewards, cues); hard to leave a bad investment (sunk cost, loss aversion, self-justification); children struggling with transitions (self-regulation, predictability, autonomy); the dependable person who cannot delegate (role identity, perceived control); choosing nothing from too many options (choice overload, including when it does and does not occur); trusting a familiar false claim (fluency, repetition); rejecting useful feedback (identity threat, trust, psychological safety); defending a purchase after paying (cognitive dissonance, post-purchase rationalization).

### Production and distribution standards from the brief
- Premium editorial look, restrained typography, consistent palette, motion only where it aids attention or understanding; essential text inside safe areas; every scene adds meaning; no unrelated footage.
- QC before publishing also covers: spelling, correct visual representation of the concept, misleading statements, excessive text, opening-frame clarity, abrupt endings.
- Caption adds context beyond the voiceover; natural search phrases when they apply (behavioral psychology, decision-making, consumer psychology, workplace behavior, parenting psychology); a few specific hashtags; source attribution.
- Never mark anything published until the platform confirms; no duplicate posts on retry; no purchases or paid upgrades without Namrata's approval.
- Success is not posting consistently. It is viewers recognizing hidden patterns in their own behavior, learning something useful, and coming back because each video rewards their attention.
