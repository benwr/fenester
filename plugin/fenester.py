import math
import sys

import vim

NONE = 0
VERTICAL = 1
HORIZONTAL = 2

DEFAULT_MIN_WIDTH = 20
DEFAULT_MIN_HEIGHT = 10

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
        self.linemax = None
        self.minwidth = None
        self.prefwidth = None
        self.focwidth = None
        self.minheight = None
        self.prefheight = None
        self.focheight = None

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

        self.width = max(self.right - self.left + 1, 0)
        self.height = max(self.bottom - self.top + 1, 0)

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
        if self.minwidth:
            return self.minwidth
        elif self.direction == NONE:
            self.minwidth = DEFAULT_MIN_WIDTH
        elif self.direction == VERTICAL:
            self.minwidth = max([l.min_width() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            self.minwidth = sum([l.min_width() for l in self.layouts])
        return self.minwidth

    def min_height(self):
        if self.minheight:
            return self.minheight
        elif self.direction == NONE:
            self.minheight = DEFAULT_MIN_HEIGHT
        elif self.direction == VERTICAL:
            self.minheight = sum([l.min_height() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            self.minheight = max([l.min_height() for l in self.layouts])

        return self.minheight
        
    def preferred_width(self):
        if self.prefwidth:
            return self.prefwidth
        elif self.direction == NONE:
            text_length = len(self.window.buffer)
            lineno_width = min(int(math.log(text_length, 10) + 2.0001), 4)
            self.linemax = self.linemax or max([len(l)
                for l in self.window.buffer])
            self.prefwidth = max(self.linemax + lineno_width
                    + 2, self.min_width() + lineno_width + 2)
        # for line numbers
        elif self.direction == VERTICAL:
            self.prefwidth = max([l.preferred_width() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            self.prefwidth = sum([l.preferred_width() for l in self.layouts])

        return self.prefwidth

    def preferred_height(self):
        if self.prefheight:
            return self.prefheight
        elif self.direction == NONE:
            self.prefheight = max(len(self.window.buffer) + 5, self.min_height() + 5)
        elif self.direction == VERTICAL:
            self.prefheight = sum([l.preferred_height() for l in self.layouts])
        else: # self.direction == HORIZONTAL:
            self.prefheight = max([l.preferred_height() for l in self.layouts])

        return self.prefheight

    def focused_width(self):
        if self.focwidth:
            return self.focwidth
        elif self.direction == NONE:
            self.focwidth = self.preferred_width()
        elif self.focused_index == -2:
            self.focwidth = self.min_width()
        elif self.direction == VERTICAL:
            self.focwidth = max([self.layouts[self.focused_index].focused_width()]
                    + [l.min_width() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])
        else: # self.direction == HORIZONTAL
            self.focwidth = sum([self.layouts[self.focused_index].focused_width()]
                    + [l.min_width() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])

        return self.focwidth

    def focused_height(self):
        if self.focheight:
            return self.focheight
        elif self.direction == NONE:
            self.focheight = self.preferred_height()
        elif self.focused_index == -1:
            self.focheight = self.min_height()
        elif self.direction == VERTICAL:
            self.focheight = sum([self.layouts[self.focused_index].focused_height()]
                    + [l.min_height() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])
        else: # self.direction == HORIZONTAL
            self.focheight = max([self.layouts[self.focused_index].focused_height()]
                    + [l.min_height() for l in
                        self.layouts[:self.focused_index] +
                        self.layouts[self.focused_index + 1:]])

        return self.focheight
    
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
            if sum(preferred_widths) <= width:
                for i, (w, l) in enumerate(zip(preferred_widths, self.layouts)):
                    if i != self.focused_index:
                        l.force_into_dimensions(w, height)
                    elif self.focused_index != -1:
                        l.force_into_dimensions(width -
                                sum(preferred_widths) +
                                preferred_widths[self.focused_index], height)
            else:
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

            if sum(preferred_heights) <= height:
                for i, (h, l) in enumerate(zip(preferred_heights, self.layouts)):
                    if i != self.focused_index:
                        l.force_into_dimensions(width, h)
                    elif self.focused_index != -1:
                        l.force_into_dimensions(width, height - sum(preferred_heights) +
                                    preferred_heights[self.focused_index])
            else:
                growth_rates = [p - m for (p, m)
                        in zip(preferred_heights, min_heights)]
                total_growth = height - sum(min_heights) 
                if sum(growth_rates) > 0:
                    growth_proportions = [float(r) / sum(growth_rates)
                            for r in growth_rates]
                else:
                    growth_proportions = [1 for _ in growth_rates]

                heights = [r * total_growth + m for (r, m)
                        in zip(growth_proportions, min_heights)]
                for h, l in zip(heights, self.layouts):
                    l.force_into_dimensions(width, int(h))
        else:
            self.window.width = width
            self.window.height = height

    def force_layout(self):
        self.force_into_dimensions(self.width, self.height)

layout = Layout(vim.windows, vim.current.window)


layout.force_layout()
