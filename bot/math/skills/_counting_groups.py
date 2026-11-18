"""Read explicit container/content relations independently of object names."""
import re


_NOUN = r'[a-z]+(?:[ -]+[a-z]+){0,5}?'
_CONTENT = (r'has|have|holds?|contains?|uses?|needs?|requires?|produces?|makes?|'
            r'carries|carry|takes?|weighs?|yields?')


def _label(tail, head, unit):
    """Keep explicit modifiers up to the noun head, when it is identifiable."""
    words = []
    for word in re.findall(r'[a-z]+|[^a-z\s-]', tail.lstrip(' -')):
        if not word.isalpha():
            break
        normalized = unit(word)
        if normalized:
            words.append(normalized)
        if normalized == head:
            return tuple(words)
    return ()


def container_relations(problem, unit, units, singular=False, postposed=True):
    """Return rate -> count edges and explicit unit-denominator references.

    ``unit`` reads a noun phrase using the caller's unit conventions. More
    than one count of a referenced group is ambiguous and is never guessed.
    An explicit "in one group" describes a denominator, not another stock.
    """
    ns = problem.numbers
    text = problem.text.lower()
    edges, references = set(), set()
    labels = [_label(text[n.end:], units[i], unit) for i, n in enumerate(ns)]
    # Resolve denominator references before looking for matching inventories.
    for i in range(len(ns)-1):
        middle = text[ns[i].end:ns[i+1].start]
        if (ns[i+1].value == 1
                and re.fullmatch(r'\s+' + _NOUN + r'\s+in\s+', middle)):
            references.add(i+1)

    for i, n in enumerate(ns):
        start = ns[i-1].end if i else 0
        end = ns[i+1].start if i+1 < len(ns) else len(problem.body)
        before = re.split(r'[.!?;](?:\s|$)', text[start:n.start])[-1]
        after = re.split(r'[.!?;](?:\s|$)|,?\s+and\b', text[n.end:end])[0]
        groups = set()
        group_labels = []
        articles = r'each|every|a|an|one' if singular else r'each|every'
        m = re.search(r'\b(?:' + articles + r')\s+(?:of\s+(?:the\s+)?)?('
                      + _NOUN + r')(?:\s+on\s+' + _NOUN + r')?\s+'
                      r'(?:(?:can|will)\s+)?(?:' + _CONTENT + r'|opened)\s*$', before)
        if m:
            groups.add(unit(m.group(1)))
            group_labels.append(m.group(1))
        # Fronted event clause: "every event she ..., she <action> N ...".
        # The repeated pronoun keeps the event and action with one subject.
        m = re.search(r'\b(?:each|every) ([a-z]+) (he|she|they|it) '
                      r"[a-z ,'-]+,\s*\2 [a-z ]+\s*$", before)
        if m:
            groups.add(unit(m.group(1)))
            group_labels.append(m.group(1))
        m = re.search(r'\bin each\s+(' + _NOUN + r'),?\s+'
                      r'(?:(?:he|she|they|it)\s+)?'
                      r'(?:opened|placed|put|has|holds|contains)\s*$', before)
        if m:
            groups.add(unit(m.group(1)))
            group_labels.append(m.group(1))
        m = re.search(r'\b(?:per|each|every|in a single|in single|in a|on a|in one)\s+('
                      + _NOUN + r')(?=[,.;!?]|$|\s+(?:in|on|at|for|with|to|where|which|that|whose|while|when|but|before|after)\b)', after)
        if postposed and m and m.group(1).split()[0] not in ('with', 'having', 'of', 'one'):
            if ',' in after[:m.start()]:
                return None  # A clause-wide rate has unresolved scope.
            qualifiers = m.group(1).split()[:-1]
            if any(w in ('other', 'alternate', 'first', 'second', 'third',
                         'fourth', 'fifth', 'sixth', 'seventh', 'eighth',
                         'ninth', 'tenth') or w.endswith(('teenth', 'tieth'))
                   for w in qualifiers):
                return None
            # "Each group has N items per row" states N per row; the
            # fronted group supplies the enclosing context, not N's unit.
            groups = {unit(m.group(1))}
            group_labels = [m.group(1)]
        if i:
            middle = text[ns[i-1].end:n.start]
            # An adjacent count and an explicitly hyphenated measurement.
            if not middle.strip() and re.match(r'-[a-z]+\b', text[n.end:]):
                edges.add((i, i-1))
            adjacent = re.fullmatch(r'\s+(' + _NOUN + r'),?\s+'
                                    r'(?:(?:with|having) (?:a )?capacity of|'
                                    r'each (?:with|having|holding|containing))\s+', middle)
            if adjacent and unit(adjacent.group(1)) == units[i-1]:
                groups.add(units[i-1])
            # N containers with M objects each.
            if (re.fullmatch(r'\s+(' + _NOUN + r')\s+with\s+', middle)
                    and re.fullmatch(r'\s+' + _NOUN + r'\s+each\s*', after)):
                groups.add(units[i-1])
            # N objects that take M units each (possibly "each to ...").
            postposed_each = re.match(r'\s+' + _NOUN + r'\s+each(?:\s+(?:to|for|and)\b|\s*$)', after)
            if (re.fullmatch(r'\s+' + _NOUN + r'\s+(?:that\s+)?'
                             r'(?:takes?|weighs?|contains?|holds?)\s+', middle)
                    and postposed_each):
                edges.add((i, i-1))
            # N items in each of the owner's M containers.
            if re.search(r'\b(?:in|on|from|for|by|with) each of\b[^.;!?]*$', middle):
                edges.add((i-1, i))
        if i+1 in references:
            groups.add(units[i+1])
        # An unresolved postposed "each" is still a rate, never loose stock.
        if (re.match(r'\s+' + _NOUN + r'\s+each(?:\s+(?:to|for|and)\b|\s*$)', after)
                and not groups and not any(rate == i for rate, count in edges)):
            return None
        groups.discard('')
        if len(groups) > 1:
            return None
        if not groups:
            continue
        group = next(iter(groups))
        matches = [j for j, u in enumerate(units)
                   if j != i and j not in references and u == group]
        qualifiers = [_label(label, group, unit) for label in group_labels]
        matches = [j for j in matches if not any(
            len(label) > 1 and len(labels[j]) > 1 and label != labels[j]
            for label in qualifiers)]
        if not matches and singular and re.search(r'\b(?:a|an|one)\s+', before):
            continue
        if len(matches) != 1:
            return None
        edges.add((i, matches[0]))
    parents = dict(edges)
    if len(parents) != len(edges):
        return None  # Conflicting denominators for the same quantity.
    return parents, references
