# RegScriptBox Constitutions

1) Purpose
1.1) This document is the single source of truth for identity, lineage, metadata, and registry standards in RegScriptBox.

2) Glossary
2.1) CID = Category ID (human-readable classification)
2.2) SID = Section ID (job identity inside a file; no hash)
2.3) PYN = Python Artifact ID (file identity; includes hash + lineage hash)
2.4) Capability = concise verb phrase describing what a section does
2.5) Hash = stable fingerprint of normalized code text
2.6) Generation = 0 means original tool file; 1+ means extracted chunk files

3) CID Constitution
3.1) Format
3.1.1) <ENV>.<NOUN>.<OBJECT>

3.2) Rules
3.2.1) ENV = domain boundary (WEB, FS, DOC, DB, API, SYS, AUTH, UI, BOT, TRADE, etc.)
3.2.2) NOUN = subsystem (DOC, PDF, MD, HTML, HTTP, SQLITE, CSV, ROUTE, etc.)
3.2.3) OBJECT = specific target (FETCH, PARSE, RENDER, INDEX, REGISTER, etc.)
3.2.4) Keep it short, consistent, and expandable.

3.3) Examples
3.3.1) WEB.DOC.PDF
3.3.2) WEB.DOC.MD
3.3.3) FS.FILE.COPY
3.3.4) DB.SQLITE.WRITE

4) SID Constitution
4.1) Definition
4.1.1) SID means “same job”.
4.1.2) If two sections do the same job, they should converge to one SID after standardization.

4.2) Format
4.2.1) <CID>|<CAPABILITY>|<ORD>

4.3) Notes
4.3.1) SID contains no hash.
4.3.2) ORD is local order within the file (01, 02, 03…).
4.3.3) CAPABILITY is a short verb phrase (examples: render_pdf, write_markdown, read_config).

4.4) Examples
4.4.1) WEB.DOC.PDF|render_pdf|03
4.4.2) WEB.DOC.MD|write_markdown|04

5) PYN Constitution
5.1) Definition
5.1.1) PYN is the file identity for standalone artifacts (tools or extracted chunk-files).

5.2) Format
5.2.1) <PYN_KIND>-G<GEN>-<CID>-<HASH>-P<PARENT_HASH>

5.3) Rules
5.3.1) GEN 0 has no parent hash.
5.3.2) GEN 1+ must include parent hash.
5.3.3) PARENT_HASH is the hash of the parent PYN string (not the parent code).
5.3.4) HASH is the code hash (normalized code body).
5.3.5) PARENT_HASH functions as the lineage pointer.

6) Hash + Lineage Constitution
6.1) Code Hash
6.1.1) Hash input is normalized.
6.1.2) Normalization includes stripping trailing whitespace.
6.1.3) Normalization includes normalizing line endings.
6.1.4) Optionally remove purely comment-only lines if policy says so.
6.1.5) Header display uses short form (typically first 12 to 16 characters).
6.1.6) Registry stores full hash.

6.2) Lineage Hash
6.2.1) Parent linkage is stored as a hash of the parent PYN string.
6.2.2) Parent pointers are followed to trace lineage back to GEN 0.

7) Metadata Constitution
7.1) Storage Rule
7.1.1) Metadata is stored in SQLite and is not bloated into headers.

7.2) Minimum Fields
7.2.1) pyn
7.2.2) gen
7.2.3) cid
7.2.4) sid
7.2.5) capability
7.2.6) hash_full
7.2.7) parent_pyn_hash (nullable)
7.2.8) file_path
7.2.9) created_at
7.2.10) updated_at

8) Registry (SQLite) Constitution
8.1) Definition
8.1.1) SQLite is the ground-truth index.

8.2) It records
8.2.1) every file (PYN)
8.2.2) every section (SID)
8.2.3) hash collisions (identicals)
8.2.4) same CID plus same capability candidates for merge review

9) Annotator Constitution
9.1) Annotator responsibilities
9.1.1) reads .py file
9.1.2) identifies sections
9.1.3) assigns CID and SID
9.1.4) computes hashes
9.1.5) writes registry entries
9.1.6) outputs annotated copy
9.1.7) never overwrites originals

10) Indexer Constitution
10.1) Indexer responsibilities
10.1.1) crawls repo
10.1.2) updates sitemap/index from registry
10.1.3) keeps human navigation fast and LLM retrieval cheap

11) Versioning + Archive Rules
11.1) Originals are preserved under archive.
11.2) Annotated outputs become canonical for new work.
11.3) Merges create a new version (new hash, new PYN).

12) Worked Examples
12.1) TBD

— Addendums —
Addendum 2026-01-29

13) Execution Scan Trigger Constitution

13.1) Definition  
The Execution Scan Trigger binds system scanning to execution events, referring executed artifacts to the annotation pipeline within applicable environments.

13.2) Scope  
The Execution Scan Trigger is reactive and environment-agnostic. It does not initiate execution and does not prevent execution.

13.3) Limits  
The Execution Scan Trigger does not interpret code, enforce policy, evaluate outcomes, or assign identity. It guarantees referral, not correctness, success, or compliance.

⸻

14) Capability Resolver Constitution

14.1) Definition  
The Capability Resolver assigns a capability label to CID-scoped code sections. A capability describes what a section of code is capable of doing, not what it ultimately produces.

14.2) Role  
The Capability Resolver operates during annotation and classification. It pairs each CID with a single capability label used for section identity, comparison, and standardization.

14.3) Limits  
The Capability Resolver does not execute code, define policy, or determine outcomes. It does not grant authority and does not alter code behavior..