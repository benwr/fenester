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
    def __init__(self, windows, focused):
        """Build the layout tree based on window positions.

        This method probably has annoying failure modes, but vim doesn't
        seem to expose its internal split tree to the plugin, so we're kinda
        restricted to doing it this way.
        """

        self.focused_index = -1

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
            if partialvsplits[w.col] >= self.height:
                verticalsplitlist.append(w.col)

        horizontalsplitlist.sort()
        verticalsplitlist.sort()

        groups = [list() for _ in (horizontalsplitlist
            if self.direction == VERTICAL else verticalsplitlist)]

        # figure out where the splits are and add windows to the right layouts
        # This is even less efficient than the above stuff, but it's probably not
        # important. It could probably be improved using `bisect`, or by just writing
        # my own damn binary search.
        for w in windows:
            if self.direction == HORIZONTAL:
                for i, col in enumerate(verticalsplitlist):
                    if col == w.col or i == len(verticalsplitlist) - 1:
                        groups[i].append(w)
                        if w == focused:
                            self.focused_index = i
                        break
                    if col > w.col:
                        groups[i - 1].append(w)
                        if w == focused:
                            self.focused_index = i - 1
                        break
            else:
                for i, row in enumerate(horizontalsplitlist):
                    if row == w.row or i == len(horizontalsplitlist) - 1:
                        groups[i].append(w)
                        if w == focused:
                            self.focused_index = i
                        break
                    if row > w.row:
                        groups[i - 1].append(w)
                        if w == focused:
                            self.focused_index = i - 1
                        break

        self.layouts = [Layout(ws, focused) for ws in groups]

    def direction_string(self):
        if self.direction == HORIZONTAL:
            return "HORIZONTAL"
        elif self.direction == VERTICAL:
            return "VERTICAL"
        else:
            return "NONE"


    def __repr__(self):
        min_dim = (self.min_height()
                if self.direction == HORIZONTAL else self.min_width())
        preferred_dim = (self.preferred_height()
                if self.direction == HORIZONTAL else self.preferred_width())
        focused_dim = (self.focused_height()
                if self.direction == HORIZONTAL else self.focused_width())
        if self.layouts:
            return "Layout({} ({}, {}, {}) : {})".format(
                    self.direction_string(), min_dim,
                    preferred_dim, focused_dim, self.layouts)
        else:
            return "Layout((({}, {}), ({}, {})) : {})".format(
                    self.min_width(), self.min_height(), self.preferred_width(),
                    self.preferred_height(), self.window)

    def min_width(self):
        if self.direction == NONE:
            return 20
        elif self.direction == VERTICAL:
            return max([l.min_width() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            return sum([l.min_width() for l in self.layouts])

    def min_height(self):
        if self.direction == NONE:
            return 10
        elif self.direction == VERTICAL:
            return sum([l.min_height() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            return max([l.min_height() for l in self.layouts])
        
    def preferred_width(self):
        if self.direction == NONE:
            return max([len(l) for l in self.window.buffer]) + 6
        # for line numbers
        elif self.direction == VERTICAL:
            return max([l.preferred_width() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            return sum([l.preferred_width() for l in self.layouts])

    def preferred_height(self):
        if self.direction == NONE:
            return len(self.window.buffer)
        elif self.direction == VERTICAL:
            return sum([l.preferred_height() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            return max([l.preferred_height() for l in self.layouts])

    def focused_width(self):
        if self.direction == NONE:
            return self.preferred_width()
        if self.focused_index == -1:
            return self.min_width()
        if self.direction == VERTICAL:
            return max([self.layouts[self.focused_index].focused_width()]
                    + [l.min_width() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])
        else: # self.direction == HORIZONTAL
            return sum([self.layouts[self.focused_index].focused_width()]
                    + [l.min_width() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])

    def focused_height(self):
        if self.direction == NONE:
            return self.preferred_height()
        if self.focused_index == -1:
            return self.min_height()
        if self.direction == VERTICAL:
            return max([self.layouts[self.focused_index].focused_height()]
                    + [l.min_height() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])
        else: # self.direction == HORIZONTAL
            return sum([self.layouts[self.focused_index].focused_height()]
                    + [l.min_height() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])
    
    def force_into_dimensions(self, width, height):
        if self.direction == HORIZONTAL:
            min_widths = [l.min_width() for l in self.layouts]
            preferred_widths = [l.preferred_width() for l in self.layouts]
            min_width = sum(min_widths)
            if min_width > width:
                raise ValueError("Not enough room to resize")
            if self.focused_index != -1:
                focused_min_width = min_widths[self.focused_index]
                focused_width = self.layouts[self.focused_index].focused_width()
                min_widths[self.focused_index] = min(width - min_width,
                        focused_width)

            growth_rates = [p - m for (p, m) in
                    zip(preferred_widths, min_widths)]
            total_growth = width - sum(min_widths) 
            growth_proportions = [float(r) / sum(growth_rates)
                    for r in growth_rates]

            widths = [r * total_growth + m
                    for (r, m) in zip(growth_proportions, min_widths)]
            for w, l in zip(widths, self.layouts):
                l.force_into_dimensions(int(w), height)
        elif self.direction == VERTICAL:
            min_heights = [l.min_height() for l in self.layouts]
            preferred_heights = [l.preferred_height() for l in self.layouts]
            min_height = sum(min_heights)
            if min_height > height:
                raise ValueError("Not enough room to resize")
            if self.focused_index != -1:
                focused_min_height = min_heights[self.focused_index]
                focused_height = (self.layouts[self.focused_index]
                        .focused_height())
                min_heights[self.focused_index] = min(height - min_height,
                        focused_height)

            growth_rates = [p - m for (p, m)
                    in zip(preferred_heights, min_heights)]
            total_growth = height - sum(min_heights) 
            growth_proportions = [float(r) / sum(growth_rates)
                    for r in growth_rates]

            heights = [r * total_growth + m for (r, m)
                    in zip(growth_proportions, min_heights)]
            for w, l in zip(heights, self.layouts):
                l.force_into_dimensions(width, int(w))
        else:
            self.window.width = width
            self.window.height = height

    def force_layout(self):
        self.force_into_dimensions(self.width, self.height)

layout = Layout(vim.windows, vim.current.window)


layout.force_layout()
