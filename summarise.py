"""Summary of results.jsonl (written by process.py)."""
import json, collections, csv
R = [json.loads(l) for l in open("results.jsonl")]
ok = [r for r in R if not r.get("empty")]
contested = [r for r in ok if len(r["candidates"]) >= 3]
year = lambda r: int(r["file"].split("_")[1][:4])
rows = []
for r in ok:
    rows.append(dict(file=r["file"], year=year(r), candidates=len(r["candidates"]), ballots=r["n_ballots"],
                     condorcet_winner=r["condorcet_winner"] or "", irv_winner=r["irv_winner"],
                     smith_set="; ".join(r["smith_set"]), irv_in_smith=r["irv_winner"] in r["smith_set"],
                     agrees=(r["condorcet_winner"] == r["irv_winner"])))
with open("summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
no_cw = [r for r in ok if r["condorcet_winner"] is None]
cycles = [r for r in no_cw if len(r["smith_set"]) >= 3]
ties = [r for r in no_cw if len(r["smith_set"]) < 3]
mism = [r for r in ok if r["condorcet_winner"] and r["condorcet_winner"] != r["irv_winner"]]
print(f"elections {len(ok)} ({min(map(year, ok))}-{max(map(year, ok))}); with 3+ candidates {len(contested)}")
print("Condorcet cycles:", [r["file"] for r in cycles])
print("Exact pairwise ties at the top:", [r["file"] for r in ties])
print("Condorcet winner exists but IRV elects someone else:", [r["file"] for r in mism])
print("IRV winner outside the Smith set:", [r["file"] for r in ok if r["irv_winner"] not in r["smith_set"]])
print("Elections 2023-2025:", sum(year(r) >= 2023 for r in ok))
