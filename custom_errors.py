class LangError(Exception):
    def __init__(self, msg, lc):
        super().__init__("\n" + msg + f"\nOccured at line: {lc[0]}, column: {lc[1]}")



        