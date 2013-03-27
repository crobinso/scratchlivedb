

class UnknownEntry(object):
    """
    Debug helper for tracking database keys we've never seen before,
    and aren't explicitly supported in the code
    """

    def __init__(self, key):
        self.key = key
        self.values = {}

    def add_example(self, filebase, val):
        """
        Add an example value for the unknown key
        """
        if val not in self.values:
            self.values[val] = []
        self.values[val].append(filebase)


class UnknownEntryTracker(object):
    def __init__(self):
        self.unknowns = {}

    def track_unknown(self, filebase, key, val):
        """
        Init an UnknownEntry for a key we've never seen before
        """
        if key not in self.unknowns:
            self.unknowns[key] = UnknownEntry(key)
        entry = self.unknowns[key]
        entry.add_example(filebase, val)
