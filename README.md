# The Unofficial Guide: UCLA Transfer Student Survival Guide

A RAG (Retrieval-Augmented Generation) system that makes student-generated knowledge about transferring to UCLA searchable and answerable. Ask a plain-language question and get a grounded, cited answer drawn from real documents collected from Reddit, Bruinwalk, and official UCLA pages.

---

## Domain and Document Sources

**Domain:** UCLA Transfer Student Survival Guide — practical knowledge for incoming transfer students at UCLA.

This knowledge is valuable because official UCLA channels tell you what exists but not what actually matters. Students can't easily search scattered Reddit threads, Bruinwalk reviews, and student blog posts with a single question. This system makes that knowledge queryable.

**Document sources:**

| # | File | Source |
|---|------|--------|
| 1 | Transfer_megathread(1).txt | r/UCLA transfer megathread |
| 2 | What_I_wish_transfer(2) | r/UCLA "What I wish I knew as a transfer" thread |
| 3 | Ucla_posts(3) | r/TransferStudents UCLA-specific posts |
| 4 | Bruinwalk(4) | Bruinwalk.com professor reviews |
| 5 | Ucla_transfer_reqs(5).txt | UCLA admissions transfer requirements page |
| 6 | Ucla_Housing(6).txt | UCLA Housing transfer students page |
| 7 | Ucla_dining(7) | UCLA Dining residential restaurants page |
| 8 | Financial_aid(8) | UCLA Financial Aid transfer students page |
| 9 | Ucla_registrar(9).txt | UCLA Registrar enrollment appointments page |
| 10 | Ucla_studentaffairs(10).txt | UCLA Student Affairs / CARE page |
| 11 | Ucla_tap(11).txt | UCLA Transfer Alliance Program page |
| 12 | What_its_like(12) | Student-written blog post on UCLA transfer experience |

---

## Chunking Strategy and Reasoning

**Chunk size:** 400 characters
**Overlap:** 80 characters

Most source documents are short-to-medium opinion and review text (1–5 sentences per thought). A 400-character chunk captures one complete idea — a single professor opinion, one piece of housing advice, one FAQ answer — without merging unrelated topics. Larger chunks risk blending a comment about enrollment deadlines with unrelated dining advice, diluting the embedding signal. Smaller chunks break sentences mid-thought and lose enough context that the model can't represent the topic reliably. The 80-character overlap ensures a key fact near a chunk boundary is retrievable from either side.

The pipeline splits on paragraph boundaries first; if a paragraph exceeds 400 characters it falls back to fixed-character splitting with overlap. Bruinwalk reviews and Reddit posts already under 300 characters are kept as single chunks.

**Total chunks produced:** 627

---

## Sample Chunks

**Chunk 1** — Source: `Transfer_megathread(1).txt`
> "Clusters also knock out a bunch of GE's, but many people have mixed opinions about them. I personally like choosing my GE's, which makes it easier to get easy GE's and better class times."

**Chunk 2** — Source: `Ucla_posts(3)`
> "I realized that because of my introverted nature and wanting to stay 'comfortable', I missed a lot of opportunities to make new friends and go outside of my comfort zone. While I did manage to join 1-2 clubs, transfers have half of the time that freshmen do so by the time you realize it, you're already one year down until graduation."

**Chunk 3** — Source: `Ucla_registrar(9).txt`
> "Transfer credit and UCLA earned units. When projecting enrollment groups, current summer units are not included."

**Chunk 4** — Source: `Ucla_studentaffairs(10).txt`
> "UCLA is a world renown university that develops so many brilliant minds, offering so many opportunities."

**Chunk 5** — Source: `Bruinwalk(4)`
> "If I took ONLY this class. We covered HTML, CSS, and JavaScript, the essentials of web programming. But we also spent the other half of the class cramming in PHP and MySQL, as well as wasting time on jQuery. Just yourself, I am warning you now."

---

## Embedding Model

**Model:** `all-MiniLM-L6-v2` via `sentence-transformers`
**Vector store:** ChromaDB (persisted to disk)

This model runs locally with no API key and no rate limits, producing 384-dimensional vectors. It is appropriate for this project given the small corpus and no budget constraints.

**Production tradeoff reflection:** For a real deployment I would weigh: (1) **accuracy** — `text-embedding-3-small` (OpenAI) produces higher-quality embeddings for longer text; (2) **cost** — API-based models add per-token cost at query time; (3) **latency** — local models add startup time but have no network round-trip; (4) **multilingual support** — if serving non-English speakers, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be necessary. For this short English review corpus, `all-MiniLM-L6-v2` is the right tradeoff.

---

## Retrieval Test Results

**Query 1:** "What is the housing lottery process for transfer students?"

Top returned chunks:
- `Ucla_Housing(6).txt` (distance: 0.919) — "Graduate and Family Housing GARs will be available once a student has an accepted offer until their contract start date. Undergraduate Room Swap and Transfer Request: During the academic year, students looking to move to a new room can submit a room swap and transfer request during each quarter."
- `What_I_wish_transfer(2)` (distance: 0.923) — "I think it's more about thinking of freshmen housing first then transfers are next priority."

These chunks are relevant — they surface the key student insight that freshmen are prioritized over transfers in housing.

**Query 2:** "What mental health resources exist for transfer students?"

Top returned chunks:
- `Ucla_studentaffairs(10).txt` — Transfer Student Center, UCLA Student Affairs support programs
- `Ucla_tap(11).txt` — Transfer Alliance Program advising resources

These chunks directly answered the question with named resources. ✅

**Query 3:** "What do students say about enrollment appointments for transfers?"

Top returned chunks:
- `Ucla_registrar(9).txt` (distance: 0.747) — enrollment appointment process description
- `Ucla_registrar(9).txt` (distance: 0.772) — graduate student enrollment passes

Retrieval found the right document but the chunks contained official procedural text, not student opinions — which is what the question asked for. The LLM correctly declined to answer rather than hallucinating student opinions.

---

## How Grounded Generation Is Enforced

The system prompt explicitly instructs the LLM to answer only from the provided document excerpts:

> "You answer questions using ONLY the provided document excerpts. Do not use any outside knowledge or make anything up. If the provided documents do not contain enough information to answer the question, say exactly: 'I don't have enough information in my documents to answer that.'"

This is enforced at the prompt level — every query passes only the top-5 retrieved chunks as context. The LLM has no access to its training knowledge for answering; if the retrieved chunks don't contain the answer, it declines. This was verified by asking "What is the capital of France?" — the system correctly refused to answer.

---

## Example Responses

**Query:** "What dining options are available at UCLA?"

**Response:**
> UCLA Dining provides a range of dining options for students, faculty, staff, and guests. During the academic school year, there are four all-you-care-to-eat residential restaurants located in Carnesale Commons, Sunset Village, Rieber Court, and De Neve Plaza. Additionally, there are quick-service locations including Bruin Café, Cafe 1919, The Drey, The Study at Hedrick, Rendezvous, Bruin Bowl, and Epicuria.
>
> Sources: • Ucla_dining(7)

**Query:** "What mental health or support resources exist specifically for transfer students?"

**Response:**
> According to the documents, there is a Transfer Student Center that provides personalized support to ensure every Bruin thrives academically and personally. Additionally, UCLA Student Affairs is available for guidance on maintaining mental well-being and meeting academic requirements.
>
> Sources: • Ucla_studentaffairs(10).txt • Ucla_tap(11).txt

**Out-of-scope query:** "What is the capital of France?"

**Response:**
> I don't have enough information in my documents to answer that.

---

## Query Interface

**Input:** A plain-language question typed into a Gradio text box.
**Output:** An answer grounded in retrieved documents, plus a "Retrieved from" panel listing source document names.

The interface is built with Gradio and runs locally at `http://127.0.0.1:7860`. Run it with:
```bash
python app.py
```

**Sample interaction transcript:**

*User:* What dining options are available at UCLA?

*System:* UCLA Dining provides a range of dining options for students, faculty, staff, and guests. During the academic school year, there are four all-you-care-to-eat residential restaurants located in Carnesale Commons, Sunset Village, Rieber Court, and De Neve Plaza...
Sources: • Ucla_dining(7)

---

## Evaluation Report

| # | Question | Expected Answer | System Response | Accuracy |
|---|----------|----------------|-----------------|----------|
| 1 | What is the housing lottery process for transfer students? | Transfers guaranteed housing first year; room selection after accepting admission; spring deadlines | Freshmen prioritized first, transfers next; transfers get "bottom of the barrel" offers since continuing students selected months in advance | **Partially accurate** |
| 2 | Which dining hall do students recommend most at UCLA, and why? | Specific hall (e.g. De Neve) with student-cited reasons | "I don't have enough information in my documents to answer that." | **Inaccurate** |
| 3 | What do students say about the enrollment appointment process for transfers? | Transfers get later appointments; impacted courses hard to get; use waitlist | "I don't have enough information in my documents to answer that." | **Inaccurate** |
| 4 | What mental health or support resources exist specifically for transfer students? | CARE office, CAPS, Transfer Student Center named | Transfer Student Center, UCLA Student Affairs cited with sources | **Accurate** |
| 5 | What are common mistakes transfer students make in their first quarter? | Student-voiced advice: missing deadlines, not going to office hours | "I don't have enough information in my documents to answer that." | **Inaccurate** |

---

## Failure Case Analysis

**Failure:** Questions 2, 3, and 5 all returned "I don't have enough information" despite retrieving plausibly relevant documents.

**Specific cause:** The evaluation questions were framed as "what do *students say*" — asking for student opinions and recommendations. However, most of the retrieved chunks for these queries came from **official UCLA pages** (registrar, dining, TAP), which contain procedural and factual text, not student opinions. The embedding model retrieved documents that were topically related (dining → dining page, enrollment → registrar page) but the *content type* didn't match what the question was asking for.

For example, Q2 asked which dining hall students *recommend* — but `Ucla_dining(7)` contains only the official list of dining locations with no student opinions. The LLM correctly identified that the retrieved context didn't contain an answer and declined rather than hallucinating.

**Root cause in the pipeline:** The document collection is imbalanced — too many official pages and not enough student-voice sources (Reddit threads, blog posts) for topics like dining preferences, enrollment experience, and first-quarter mistakes. Better coverage of these topics in the Reddit documents would fix this.

---

## Spec Reflection

**One way the spec helped:** Writing the chunking strategy in `planning.md` before coding forced me to think about document structure first. Because I had already decided on 400-character paragraph-first chunking, I didn't need to make that decision mid-implementation — I just coded what the spec said. This prevented the common mistake of defaulting to arbitrary chunk sizes.

**One way implementation diverged:** The spec suggested that evaluation Q5 ("common mistakes") would be a designed failure case due to broad phrasing. In practice, Q2 and Q3 also failed — not because they were too broad, but because the document collection lacked student-opinion content for those topics. The failure was a data coverage problem, not a retrieval problem as originally anticipated.

---

## AI Usage

**Instance 1 — Ingestion and chunking script:** I gave Claude my Documents section, Chunking Strategy section, and pipeline diagram from `planning.md`, and asked it to implement `ingest.py` with paragraph-first splitting and 400-character/80-overlap chunking. It produced a working script. I then ran it, identified that Reddit usernames (`jpark9`, `6y ago`) and PDF artifacts (rows of dots, stray page numbers) were slipping through, and directed Claude to add specific regex patterns to catch those. I verified the fix by re-running and inspecting 5 sample chunks.

**Instance 2 — Embedding and retrieval script:** I gave Claude my Retrieval Approach section and architecture diagram and asked it to implement `embed.py` using `all-MiniLM-L6-v2` and ChromaDB with `source` and `chunk_index` metadata. It produced a working script. I changed the import path from `ingest` to `ingest_1` to match my actual filename, and verified retrieval by running 3 test queries and checking that returned chunks were topically relevant.
