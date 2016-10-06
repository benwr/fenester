# Fenester

A Vim plugin for resizing windows in a sane way

## Rationale

Like a lot of my recent personal projects, this project
is inspired by my lack of a large enough working memory.

It's difficult for me to keep all the things I want to
in my head at once: Typically I need to remember
between 3 and 10 different scopes and data types
in mind at once. This is, perhaps, indicative that
I'm not good at designing code, but I have to deal
with it gracefully nonetheless.

Vim windows can help: If you can have multiple text
buffers on the screen at once, who needs to remember
anything?

But there are two problems with this:

1. Vim has really annoying algorithms for resizing
splits, especially when the window changes shape.
2. You can only fit a fairly small number of windows
in your tab/frame at once.

I recently stumbled upon the `golden-ratio` plugin,
which _kind of_ fixes these problems, but has
_extremely_ annoying defaults, in my opinion.

So I made something with saner defaults.


## Design

Fenester tries to force your windows to be reasonable
shapes. Windows are sized according to their contents;
i.e. a window with 80-character lines will naturally
scale up more slowly than a window with 100-character
lines.

Fenester first tries to ensure that the focused window
has its text entirely visible. Once that's accomplished,
it tries to ensure that the other windows also have
their text visible. If that's also possible, it uses
the focused window to fill the rest of the space.

There are some complexities hidden by the above
description, but it's what I was trying to approximate
when writing the plugin.

## Current issues

* Fenester is written entirely for me. It is, therefore,
entirely non-configurable - when I want to tweak
a value, I edit the source.

* It is also _ridiculously_ slow. It could easily be
sped up by actually thinking about the algorithms
involved, or by doing something even simpler (e.g.
memoizing functions)

* The code is *terrible*. I hacked this together as
fast as I could, and never looked back.

* There may be some subtle off-by-one errors in the code.
In fact, I'm pretty sure there are.

* I mostly don't care if other people use fenester,
so I haven't created a fancy screencast or anything.
If you want to make one, or if you want me to make one,
I'd probably be happy to. I just have to find some spare
time around somewhere.

If you want to address any of these issues (without
modifying the default behavior too much - remember,
this is a project entirely written for me), I'll gladly
accept any and all PRs.

