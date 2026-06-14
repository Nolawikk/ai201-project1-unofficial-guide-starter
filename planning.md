# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**UCLA Transfer Student Survival Guide** — practical, student-generated knowledge for incoming transfer students at UCLA.

This knowledge is valuable because official UCLA channels (the Transfer Center website, admissions pages, housing portal) tell you *what exists* but not *what actually matters*. They won't tell you that Hedrick dining hall gets overcrowded at 6pm, that the waitlist for impacted CS upper-divs moves slowly, or that transfer students often miss the IGETC certification deadline. That kind of knowledge lives in Reddit threads, Bruinwalk reviews, and student-written guides — scattered, unindexed, and impossible to search with a single question.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | r/UCLA — transfer megathread | Pinned annual thread with FAQs and advice from transfers |https://www.reddit.com/r/ucla/comments/g6c2ov/welcome_new_transfers_and_incoming_freshman_ask/|
| 2 | r/UCLA — "What I wish I knew as a transfer" | High-upvote advice posts from transfer students |https://www.reddit.com/r/ucla/comments/1dq17ox/psa_to_all_transfer_housing/ |
| 3 | r/UCLA — UCLA posts | Threads about housing, registration, and first-quarter tips | https://www.reddit.com/r/ucla/comments/1dvxulq/transfers_what_is_something_good_or_bad_you_only/|
| 4 | Bruinwalk.com — professor reviews | Student reviews of popular transfer-heavy CS and Math courses | https://www.bruinwalk.com |
| 5 | UCLA Transfer Center website | Official orientation checklist, deadlines, and resources | https://www.transfer.ucla.edu |
| 6 | UCLA Housing — transfer students page | Room types, housing lottery info, deadlines for transfers | https://www.housing.ucla.edu/undergraduate-housing/transfer-students |
| 7 | UCLA Dining — residential restaurants | Hours, locations, and dining plan info | https://dining.ucla.edu/residential-restaurants/ |
| 8 | UCLA Financial Aid — transfer students | Grant info, award timeline, common mistakes | https://financialaid.ucla.edu/types-of-aid/transfer-students |
| 9 | UCLA Registrar — enrollment appointments | How priority enrollment works, add/drop deadlines | https://registrar.ucla.edu/registration-classes/enrollment-appointments |
| 10 | UCLA CARE / Student Affairs | Mental health resources and transfer-specific support programs | https://www.studentaffairs.ucla.edu/support/care |
| 11 | UCLA Transfer Alliance Program | Transfer-specific academic pathways and advising info | https://www.tap.ucla.edu |
| 12 | Student-written transfer guide (blog) | Personal narrative covering first-quarter survival tips | https://medium.com/search?q=UCLA+transfer+student+guide |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 80 characters

**Reasoning:** Most source documents are short-to-medium opinion and review text (1–5 sentences per thought). A 400-character chunk (~60–80 words) captures one complete idea — a single professor opinion, one piece of housing advice, one FAQ answer — without merging unrelated topics into a single embedding. Larger chunks (800+ chars) risk blending a comment about enrollment deadlines with unrelated dining advice, diluting the embedding signal. Smaller chunks (under 200 chars) break sentences mid-thought and lose enough context that the model can't represent the topic reliably. The 80-character overlap ensures a key fact near a chunk boundary (e.g., a deadline mentioned at the end of one chunk and elaborated at the start of the next) is retrievable from either side. Bruinwalk reviews and Reddit posts that are already under 300 characters will be kept as single chunks rather than split further.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:** `all-MiniLM-L6-v2` runs locally with no API key and no rate limits, which makes it appropriate for this project. For a real production deployment, I would weigh: (1) **accuracy** — `text-embedding-3-small` (OpenAI) produces higher-quality embeddings for longer, more complex text; (2) **cost** — API-based models add per-token cost at query time; (3) **latency** — local models add startup time but have no network round-trip; (4) **multilingual support** — if the system served non-English speakers, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be necessary. For this corpus (short English reviews and FAQs), `all-MiniLM-L6-v2` is the right tradeoff.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is the housing lottery process for transfer students at UCLA? | Transfers are generally guaranteed housing for their first year; room selection happens after accepting admission; specific spring deadlines apply |
| 2 | Which dining hall do students recommend most at UCLA, and why? | A specific hall (e.g., De Neve or Epicuria) should appear with student-cited reasons like food variety, hours, or location proximity |
| 3 | What do students say about the enrollment appointment process for transfers? | Transfers often get a later appointment than continuing students; impacted courses are hard to get into; advice includes using the waitlist aggressively |
| 4 | What mental health or support resources exist specifically for transfer students? | CARE office, CAPS (Counseling & Psychological Services), Transfer Student Center — at least one specific named resource must be cited |
| 5 | What are common mistakes transfer students make in their first quarter? | Missing add/drop deadlines, not visiting office hours, underestimating workload, not using the Transfer Center — must be student-voiced advice, not generic tips |

*Question 5 is intentionally broad and designed to surface a failure case — retrieval may return loosely related chunks if documents don't cover this directly.*

---

## Anticipated Challenges

1. **Noisy Reddit and review text:** Reddit posts include upvote counts, usernames, crosstalk, and meta-commentary that isn't useful content. Bruinwalk pages include navigation elements and rating widgets. Cleaning must strip all of this without removing the actual student advice. If cleaning is incomplete, chunks will contain HTML artifacts or boilerplate that poisons the embeddings and causes off-topic retrieval.

2. **Short documents embedding poorly:** Bruinwalk reviews are often under 150 characters — too short to carry meaningful semantic signal on their own. Very short chunks risk high distance scores on all queries, meaning the retrieval system can't distinguish which professor review is relevant. I may need to concatenate reviews by professor or filter out reviews under a minimum length threshold.

---

## Architecture

```
Raw Documents (txt / scraped HTML)
          │
          ▼
┌───────────────────────┐
│   Ingestion & Clean   │  Python script — strip HTML tags, nav text,
│                       │  usernames, vote counts, HTML entities
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Chunking            │  400-char chunks, 80-char overlap,
│                       │  paragraph-first with fixed-char fallback
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Embedding           │  all-MiniLM-L6-v2
│                       │  via sentence-transformers
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Vector Store        │  ChromaDB (persisted to disk)
│                       │  metadata: source, chunk_index, doc_type
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Retrieval           │  retrieve(query, k=5)
│                       │  returns chunks + source metadata
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Generation          │  Groq llama-3.3-70b-versatile
│                       │  grounded system prompt — answer from context only
└───────────────────────┘
          │
          ▼
┌───────────────────────┐
│   Query Interface     │  Gradio web UI
│                       │  inputs: question | outputs: answer + sources
└───────────────────────┘
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I will give Claude my Documents section (file types and sources), my Chunking Strategy section, and a sample of raw Reddit/HTML text. I will ask it to implement a `ingest.py` script that loads each document, strips noise (HTML tags, nav text, usernames, vote counts), and produces clean chunks matching my 400-character size and 80-character overlap spec. I will verify the output by printing 5 random chunks and checking that each is readable, self-contained, and free of HTML artifacts.

**Milestone 4 — Embedding and retrieval:**
I will give Claude my Retrieval Approach section and my architecture diagram. I will ask it to implement an `embed.py` script that loads chunks from the ingestion pipeline, embeds them with `all-MiniLM-L6-v2`, and stores them in ChromaDB with `source`, `chunk_index`, and `doc_type` metadata. I will also ask it to implement a `retrieve(query, k=5)` function. I will verify by running 3 of my evaluation questions and checking that returned chunks visibly relate to the query and have distance scores below 0.5.

**Milestone 5 — Generation and interface:**
I will give Claude my grounding requirement (answer only from retrieved context; say "I don't have enough information" if context doesn't cover it), my desired output format (answer + source list), and the Gradio skeleton from the project spec. I will ask it to wire retrieval and generation into a working `app.py`. I will verify grounding by asking a question my documents don't cover and confirming the system declines to answer rather than hallucinating.
