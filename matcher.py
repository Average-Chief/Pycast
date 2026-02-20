def fuzzy_score(q, name):
    n = name.lower()
    q = q.lower()

    if q == n:          return 4
    if n.startswith(q): return 3
    if q in n:          return 2

    it = iter(n)
    if all(c in it for c in q): return 1

    return 0


def get_matches(query, commands):
    q = query.strip()

    if not q:
        return sorted(commands.keys())

    scored = [(fuzzy_score(q, k), k) for k in commands if fuzzy_score(q, k) > 0]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [k for _, k in scored]