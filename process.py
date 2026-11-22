"""Condorcet analysis of every single-winner RCV election in Otis's Dataverse collection.

For each cast-vote record: clean the ballots, build the pairwise-preference matrix, find the
Condorcet winner (or the Smith set when there is a cycle), run sequential-elimination IRV,
and record whether the IRV winner is the Condorcet winner.

Ballot cleaning (stated so it can be varied): a skipped rank is ignored; an overvote ends the
ballot at that rank; a repeated candidate counts only at its first rank; all write-ins form one
candidate. Unranked candidates sit below every ranked candidate on that ballot.

Usage: python process.py            (downloads each file, processes it, deletes the raw file)
"""
import csv, json, os, subprocess, sys, itertools, collections
import numpy as np

csv.field_size_limit(sys.maxsize)
META = json.load(open("meta.json"))["data"]["latestVersion"]["files"]
OUT = "results.jsonl"
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)["file"] for l in open(OUT)}

SKIP = {"skipped", "skip", "undervote", "blank", ""}
OVER = {"overvote", "over vote", "over-vote"}
WRITEIN = ("writein", "write-in", "write in", "uwi", "undeclared write")


def clean(name):
    n = name.strip().strip('"').strip()
    low = n.lower()
    if low in SKIP:
        return None
    if low in OVER:
        return "__OVER__"
    if low.startswith(WRITEIN) or low == "write-ins":
        return "Write-in"
    return n


def ballots(path):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f, delimiter="\t")
        head = next(r)
        cols = [i for i, h in enumerate(head) if h.lower().startswith("rank")]
        for row in r:
            seq, seen = [], set()
            for i in cols:
                if i >= len(row):
                    break
                c = clean(row[i])
                if c is None:
                    continue
                if c == "__OVER__":
                    break
                if c not in seen:
                    seen.add(c)
                    seq.append(c)
            yield tuple(seq)


def analyse(counter):
    cands = sorted({c for b in counter for c in b})
    k = len(cands)
    if k == 0:
        return dict(candidates=[], n_ballots=int(sum(counter.values())), empty=True,
                    condorcet_winner=None, irv_winner=None)
    ix = {c: i for i, c in enumerate(cands)}
    P = np.zeros((k, k), np.int64)          # P[a, b]: ballots ranking a above b
    for b, w in counter.items():
        ranked = [ix[c] for c in b]
        rset = set(ranked)
        unranked = [i for i in range(k) if i not in rset]
        for p, a in enumerate(ranked):
            for bb in ranked[p + 1:]:
                P[a, bb] += w
            for bb in unranked:
                P[a, bb] += w
    beats = P > P.T
    cw = [cands[a] for a in range(k) if all(beats[a, b] for b in range(k) if b != a)]
    weak = [cands[a] for a in range(k) if all(P[a, b] >= P[b, a] for b in range(k) if b != a)]
    cl = [cands[a] for a in range(k) if all(beats[b, a] for b in range(k) if b != a)]
    # Smith set: smallest set beating everyone outside it; via Copeland-ordered growth
    cop = sorted(range(k), key=lambda a: -int(beats[a].sum()))
    S = set(range(k))
    for m in range(1, k + 1):
        S = set(cop[:m])
        if all(P[a, b] > P[b, a] for a in S for b in range(k) if b not in S):
            # extend with any ties at the boundary
            break
    smith = sorted(cands[a] for a in S)
    # IRV: eliminate the lowest each round (ties broken by fewest first-round votes, then name)
    alive = set(cands)
    rounds = []
    fr = collections.Counter()
    for b, w in counter.items():
        if b:
            fr[b[0]] += w
    while True:
        tally = collections.Counter({c: 0 for c in alive})
        for b, w in counter.items():
            for c in b:
                if c in alive:
                    tally[c] += w
                    break
        cont = sum(tally.values())
        top, topv = max(tally.items(), key=lambda kv: (kv[1], kv[0]))
        rounds.append(dict(tally))
        if topv * 2 > cont or len(alive) <= 2:
            if len(alive) == 2 and topv * 2 <= cont:
                top = max(alive, key=lambda c: (tally[c], fr[c], c))
            winner = top
            break
        low = min(alive, key=lambda c: (tally[c], fr[c], c))
        alive.discard(low)
    margin_pairs = {f"{cands[a]} > {cands[b]}": [int(P[a, b]), int(P[b, a])]
                    for a, b in itertools.combinations(range(k), 2)}
    return dict(candidates=cands, n_ballots=int(sum(counter.values())),
                n_blank=int(counter.get((), 0)), condorcet_winner=cw[0] if cw else None,
                weak_condorcet=weak, condorcet_loser=cl[0] if cl else None, smith_set=smith,
                irv_winner=winner, irv_rounds=len(rounds), irv_final=rounds[-1],
                first_round_leader=max(fr, key=lambda c: (fr[c], c)) if fr else None,
                pairwise=margin_pairs)


def main(limit=None):
    todo = [f["dataFile"] for f in META if f["dataFile"]["filename"] not in done]
    todo.sort(key=lambda d: d.get("filesize", 0))
    for n, df in enumerate(todo[:limit]):
        path = "raw.tab"
        r = subprocess.run(["curl", "-s", "-f", "-L", "-m", "1800", "-o", path,
                            f"https://dataverse.harvard.edu/api/access/datafile/{df['id']}"])
        if r.returncode != 0:
            print("FAIL download", df["filename"], flush=True)
            continue
        counter = collections.Counter(ballots(path))
        res = analyse(counter)
        res["file"] = df["filename"]
        with open(OUT, "a") as f:
            f.write(json.dumps(res) + "\n")
        os.remove(path)
        flag = "" if res["condorcet_winner"] == res["irv_winner"] else "  <-- IRV != Condorcet"
        print(f"{n + 1}/{len(todo)} {df['filename']}: CW={res['condorcet_winner']} IRV={res['irv_winner']}{flag}",
              flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
