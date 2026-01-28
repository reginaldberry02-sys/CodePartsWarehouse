FILE IDENTITY CONSTITUTION
==========================

Purpose
-------
This constitution defines how all Python artifacts (files and sections)
are identified, categorized, versioned, and traced across time.

The goal is to:
- Eliminate redundant code
- Enable deterministic merging and extraction
- Preserve lineage without ambiguity
- Reduce LLM token waste
- Prevent identity drift

This system prioritizes mechanical truth over semantic guesswork.


IDENTITY LAYERS
---------------

Identity is composed of four layers:

1) CID  – Capability Identifier (category)
2) SID  – Section Identifier (job-level)
3) HASH – Canonical code fingerprint
4) PYN  – Python Identification Number (artifact identity)


1. CID (Capability Identifier)
-----------------------------

Definition:
CID classifies *what kind of job* code is meant to perform.

CID is taxonomy, not identity.

Constitution:
<CID> = <ENV>.<NOUN>.<OBJECT>

Examples:
- WEB.DOC.PDF
- DATA.ETL.LOAD
- FS.FILE.COPY

Rules:
- Human-readable
- Stable over time
- Many sections/files may share a CID
- CID alone never implies sameness of implementation


2. SID (Section Identifier)
--------------------------

Definition:
SID identifies a specific job performed by a section *within a file*.

SID exists to detect duplication and force reconciliation.

Constitution:
<SID> = <CID>|<CAPABILITY>|<ORDINAL>

Examples:
- WEB.DOC.PDF|render_pdf|03
- WEB.DOC.MD|write_markdown|04

Rules:
- No hashes
- No lineage
- Ordinal is local to the file
- Two sections with the same SID must be merged or reconciled
- SIDs may disappear after merges
- At steady state, one SID per job


3. HASH (Canonical Fingerprint)
-------------------------------

Definition:
A hash is an objective fingerprint of canonicalized code.

Purpose:
Determine whether two pieces of code are materially identical.

Rules:
- Generated after canonicalization
- Ignores whitespace, comments, formatting
- Same logic → same hash
- Different logic → different hash
- Hash has no semantic meaning


4. PYN (Python Identification Number)
------------------------------------

Definition:
PYN uniquely identifies a Python artifact (file or extracted chunk).

PYN encodes identity and lineage.

Constitution:
PYN:<K><G>|<CID>|H=<HASH>|PH=<PARENT_HASH?>

Where:
- K  = Kind (T = Tool, C = Chunk)
- G  = Generation number (0,1,2…)
- CID = Primary capability category
- H  = Hash of this artifact’s canonical code
- PH = Hash of parent PYN (only if G > 0)

Examples:
Gen0 Tool:
PYN:T0|WEB.DOC.ARCHIVE|H=7f3c2a91b4

Gen1 Chunk:
PYN:C1|WEB.DOC.RENDER|H=19ac00fe21|PH=7f3c2a91b4

Rules:
- Deterministic
- Immutable once written
- Parent hash only (no grandparents)
- Absence of PH implies Generation 0


ANNOTATOR ROLE
--------------

The annotator is a passive observer and injector.

Responsibilities:
- Parse files
- Identify sections
- Assign CID and SID
- Canonicalize code
- Generate hashes
- Generate PYNs
- Inject headers
- Emit metadata to registry

Non-responsibilities:
- No merging
- No optimization
- No decision-making


REGISTRY ROLE
-------------

The registry is a historical ledger.

It stores:
- PYNs
- SIDs
- Hashes
- Parent relationships
- Status flags (active, merged, deprecated)

Rules:
- Nothing is deleted
- Superseded artifacts are marked inactive
- Git remains the authoritative source


MERGE / EXTRACT ESCALATION
--------------------------

Triggered when:
- Same CID + same capability
- Different hashes
- Repeated variant introduction

Decisions are handled by a separate LLM-assisted agent.

Outcomes:
1) Discard inferior variant
2) Select superior implementation
3) Merge implementations
4) Recommend extraction into a new artifact

The agent outputs code and reasoning only.
Identity injection happens afterward.


END OF CONSTITUTION
