import vim
import sys

NONE = 0
VERTICAL = 1
HORIZONTAL = 2

class Layout(object):
    """Either a window or a collection of layouts (in a tree).

    If a collection of layouts, all immediate childen must be arranged
    along the same axis (horizontally or vertically).
    """
    def __init__(self, windows):
        """Build the layout tree based on window positions.

        This method probably has annoying failure modes, but vim doesn't
        seem to expose its internal split tree to the plugin, so we're kinda
        restricted to doing it this way.
        """

        # I think this function ends up being unnecessarily expensive (n^2 * log n?)
        # but it was the first thing I thought of, and n^2 * log n is still smallish for
        # the number of windows that reasonably fits on a screen (20? 50?), 
        self.top = sys.maxint
        self.left = sys.maxint
        self.bottom = 0
        self.right = 0
        for w in windows:
            if w.row < self.top:
                self.top = w.row
            if w.col < self.left:
                self.left = w.col
            if w.row + w.height > self.bottom:
                self.bottom = w.row + w.height - 1
            if w.col + w.width > self.right:
                self.right = w.col + w.width - 1

        self.width = self.right - self.left + 1
        self.height = self.bottom - self.top + 1

        if len(windows) == 1:
            self.window = windows[0]
            self.direction = NONE
            self.layouts = []
            return

        # There is probably a more efficient way to do the following (it's n^2),
        # but this is simple, and there are rarely lots of windows.

        self.direction = HORIZONTAL
        partialhsplits = {}
        horizontalsplitlist = []
        partialvsplits = {}
        verticalsplitlist = []

        for w in windows:
            # Looking for a column dividing line (other than the ones that exist at the
            # left and right) spanning the whole left-to-right
            # distance. If one exists, this can be split along horizontal
            # borders.

            partialvsplits[w.col] = partialvsplits.get(w.col, 0) + w.height + 1
            partialhsplits[w.row] = partialhsplits.get(w.row, 0) + w.width + 1

            if partialhsplits[w.row] >= self.width:
                horizontalsplitlist.append(w.row)
                if w.row != self.top:
                    # Found one!
                    self.direction = VERTICAL
            if w.col != self.top and partialvsplits[w.col] >= self.height:
                verticalsplitlist.append(w.col)

        horizontalsplitlist.sort()
        verticalsplitlist.sort()
        

        groups = [list() for _ in (horizontalsplitlist if self.direction == VERTICAL else verticalsplitlist)]

        # figure out where the splits are and add windows to the right layouts
        # This is even less efficient than the above stuff, but it's probably not
        # important. It could probably be improved using `bisect`.
        for w in windows:
            if self.direction == HORIZONTAL:
                for i, col in enumerate(verticalsplitlist):
                    if col == w.col or i == len(verticalsplitlist) - 1:
                        groups[i].append(w)
                        break
                    if col > w.col:
                        groups[i - 1].append(w)
                        break
            else:
                for i, row in enumera)te(horizontalsplitlist):
                    if row == w.row or i == len(horizontalsplitlist) - 1:
                        groups[i].append(w)
                        break
                    if row > w.row:
                        groups[i - 1].append(w)
                        break

        self.layouts = [Layout(ws) for ws in groups]

    def direction_string(self):
        if self.direction == HORIZONTAL:
            return "HORIZONTAL"
        elif self.direction == VERTICAL:
            return "VERTICAL"
        else:
            return "NONE"


    def __repr__(self):
        if self.layouts:
            return "Layout({} : {})".format(self.direction_string(), self.layouts)
        else:
            return "Layout({})".format(self.window)

