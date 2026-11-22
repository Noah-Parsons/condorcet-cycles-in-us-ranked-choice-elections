"""Re-run the notable and closest elections under alternative ballot-cleaning rules."""
import json, subprocess, collections, csv, sys
import process as P

FILES = ["Burlington_20090303_Mayor.tab", "Alaska_20220816_USHouse_Special.tab",
         "Minneapolis_20211102_CityCouncilWard2.tab", "PortlandME_20211102_CityCouncilAL.tab",
         "Oakland_20221108_SchoolBoardD4.tab", "NewYorkCity_20210622_REP_CityCouncilD15.tab",
         "Alaska_20221108_HouseDistrict15.tab", "Minnetonka_20231107_CityCouncilWard3.tab",
         "Alaska_20241105_StateHouseD28.tab", "Corvallis_20221108_Mayor.tab"]
ids = {f["dataFile"]["filename"]: f["dataFile"]["id"] for f in P.META}


def ballots(path, rule):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f, delimiter="\t")
        head = next(r)
        cols = [i for i, h in enumerate(head) if h.lower().startswith("rank")]
        for row in r:
            seq, seen, over = [], set(), False
            for i in cols:
                if i >= len(row):
                    break
                c = P.clean(row[i])
                if c is None:
                    if rule == "two_skips_exhaust" and seq is not None:
                        pass
                    continue
                if c == "__OVER__":
                    over = True
                    if rule in ("base", "two_skips_exhaust"):
                        break
                    continue            # rule "overvote_skipped": ignore the overvoted rank
                if c not in seen:
                    seen.add(c)
                    seq.append(c)
            if rule == "drop_overvoted" and over:
                continue
            yield tuple(seq)


out = []
for fn in FILES:
    subprocess.run(["curl", "-s", "-f", "-L", "-m", "1800", "-o", "raw.tab",
                    f"https://dataverse.harvard.edu/api/access/datafile/{ids[fn]}"], check=True)
    for rule in ("base", "overvote_skipped", "drop_overvoted"):
        res = P.analyse(collections.Counter(ballots("raw.tab", rule)))
        top = [k for k in res["pairwise"] if "Write-in" not in k]
        out.append(dict(file=fn, rule=rule, cw=res["condorcet_winner"], irv=res["irv_winner"],
                        smith=res["smith_set"], n=res["n_ballots"]))
        print(fn, rule, "CW:", res["condorcet_winner"], "IRV:", res["irv_winner"], "Smith:", res["smith_set"], flush=True)
json.dump(out, open("robustness.json", "w"), indent=1)
