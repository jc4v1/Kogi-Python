from Semantics.enums import ElementStatus


class MarkingGm:
    def __init__(self, markings: dict[str, ElementStatus]):
        self._markings = markings
        self._hash = None

    def markings(self) -> dict[str, ElementStatus]:
        return self._markings

    def get_element_status(self, element: str) -> ElementStatus:
        return self._markings[element]

    def __getitem__(self, key: str) -> ElementStatus:
        return self.get_element_status(key)

    def __str__(self):
        items = [f"{key}={self._format_status(value)}" for key, value in sorted(self._markings.items())]
        if not items:
            return "<>"
        return f"<{', '.join(items)}>"

    def __repr__(self):
        return f"MarkingGm(gm={self.markings()})"

    def __eq__(self, other):
        if not isinstance(other, MarkingGm):
            return NotImplemented
        return self._markings == other._markings

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(self._markings.items()))
        return self._hash

    def _format_status(self, status):
        if isinstance(status, ElementStatus):
            if status == ElementStatus.UNKNOWN:
                return "\U0001d54c"
            elif status == ElementStatus.SATISFIED:
                return "\U0001d54a"
            elif status == ElementStatus.PENDING:
                return "\u2119"
            elif status == ElementStatus.DENIED:
                return "\U0001d53b"
        return str(status)

    def __lt__(self, other):
        if not isinstance(other, MarkingGm):
            return NotImplemented
        return str(self) < str(other)


class MarkingPn:
    def __init__(self, markings: dict[str, int]):
        self._markings = dict(markings)

    def markings(self) -> dict[str, int]:
        return self._markings

    def __eq__(self, other):
        return isinstance(other, MarkingPn) and self._markings == other._markings

    def __hash__(self):
        return hash(frozenset(self._markings.items()))

    def __repr__(self):
        return f"MarkingPn({self._markings})"

    def __str__(self):
        marked_places = [p for p, v in sorted(self._markings.items()) if v == 1]
        return "{" + ", ".join(marked_places) + "}"

    def __lt__(self, other):
        if not isinstance(other, MarkingPn):
            return NotImplemented
        self_items = sorted(self._markings.items())
        other_items = sorted(other._markings.items())
        return self_items > other_items


class Marking:
    def __init__(self, gm_marking: MarkingGm, pn_marking: MarkingPn):
        self.gm_marking = gm_marking
        self.pn_marking = pn_marking

    def __eq__(self, other):
        return (
            isinstance(other, Marking)
            and self.gm_marking == other.gm_marking
            and self.pn_marking == other.pn_marking
        )

    def __hash__(self):
        return hash((self.gm_marking, self.pn_marking))

    def __repr__(self):
        return f"Marking(gm={self.gm_marking}, pn={self.pn_marking})"

    def __str__(self):
        return str(self.pn_marking)

    def __lt__(self, other):
        if not isinstance(other, Marking):
            return NotImplemented
        return (str(self.gm_marking), str(self.pn_marking)) < (str(other.gm_marking), str(other.pn_marking))

    def satisfies_quality(self, quality):
        return self.gm_marking[quality] == ElementStatus.SATISFIED
