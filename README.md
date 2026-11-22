# Condorcet cycles in US ranked-choice elections

Noah Parsons. Results as of 21 November 2026.

## Question

How often does a US ranked-choice (instant-runoff) election fail to elect the Condorcet winner, the candidate who beats every other head to head? And how often is there no Condorcet winner at all? This study covers every single-winner election in the most complete public collection of cast-vote records, through 2025.

## Sources

Deb Otis (FairVote), *Single winner ranked choice voting CVRs*, Harvard Dataverse, version 25 (24 September 2025), https://doi.org/10.7910/DVN/AMK8PJ. The collection holds 607 files; 606 contain ballots. They run from 2004 to 2025 and include 183 elections from 2023 to 2025.

## Method (`process.py`)

For each election:
1. Clean the ballots.
   - A skipped rank is ignored.
   - An overvote ends the ballot at that rank.
   - A repeated candidate counts only at its first rank.
   - All write-ins are treated as a single candidate.
   - On each ballot, unranked candidates sit below every ranked candidate.
2. Build the full pairwise-preference matrix.
3. Find the Condorcet winner, or the Smith set when there is none.
4. Run sequential-elimination IRV.

`robust.py` re-runs the notable and closest elections under two other overvote rules: skipping the overvoted rank, and discarding the ballot. `summarise.py` writes `summary.csv`, with one row per election.

**Check:** the reconstruction reproduces the known outcomes of the elections discussed below. In particular, it reproduces exactly the 8,529 to 8,529 tie in Portland, Maine's 2021 at-large council race, which the city first settled by drawing lots and then by recount.

## Results

Of 606 elections (529 with three or more candidates):

| Outcome | Elections |
|---|---|
| Condorcet winner exists and IRV elects them | 601 |
| Condorcet winner exists but IRV elects someone else | 2: Burlington, VT, mayor 2009 (Montroll beats all; Kiss elected); Alaska US House special, August 2022 (Begich beats all; Peltola elected) |
| No Condorcet winner: a cycle | 2: Minneapolis Ward 2, 2021; Oakland School Board District 4, 2022 |
| No Condorcet winner: an exact tie at the top | 1: Portland, ME, at-large council 2021 (Mazer and Rodriguez tie 8,529 to 8,529 head to head) |

- **Every IRV winner except the two failures lies in the Smith set.**
- **No new failure or cycle appears in 2023 to 2025.** The 183 elections from those three years, including the 2025 New York City mayoral primary, all have a Condorcet winner, and IRV elects them.
- **The results do not depend on how overvotes are handled.** They hold under all three cleaning rules. The one exception is Portland 2021, where the tie is so exact that any change to the ballot rules breaks it: under the other two rules, Mazer becomes both the Condorcet and the IRV winner. The official recount gave the seat to Rodriguez.

## Relation to earlier work

The two failures and both cycles are already documented. The Minneapolis cycle was reported in earlier work cited by McCune, and McCune documented Oakland's in *Ranked Choice Bedlam in a 2022 Oakland School Director Election* (arXiv:2303.05985). This study confirms those findings independently. It also extends the check, under stated and varied ballot rules, to every election in the collection through September 2025, and finds nothing new in the most recent three years. It is a replication and extension, not a new discovery.

## Reproducing

```
python process.py     # downloads each cast-vote record from Dataverse, analyses it, deletes the raw file
python robust.py      # the notable and closest elections under other ballot rules
python summarise.py   # summary.csv and the counts above
```

`process.py` resumes where it left off. The full run downloads about 600 files and takes a few hours. Python packages: numpy.

## Sources

Deb Otis (FairVote), *Single winner ranked choice voting CVRs*, Harvard Dataverse, https://doi.org/10.7910/DVN/AMK8PJ. The raw ballot files are not included. `results.jsonl` holds the derived pairwise matrices and tallies for every election.

## Files

| File | Contents |
|---|---|
| `process.py` | Downloads each CVR from Dataverse, analyses it and deletes the raw file |
| `robust.py`, `robustness.json` | Alternative ballot rules for the notable elections |
| `summarise.py`, `summary.csv` | Per-election summary |
| `results.jsonl` | Full results, including the pairwise matrix and final IRV round for every election |
| `meta.json` | Dataverse file listing |
