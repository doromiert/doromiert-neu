---
title: ZenOS
icon: zenos
tags: Operating Systems, Negative Zero, Software, Design
---

I was 8 years old, bored in świetlica, drawing an operating system on paper.

Not a game. Not a cartoon. An operating system — complete with a taskbar, window chrome, and an accent color I borrowed from Ubuntu without knowing what Ubuntu was. I called it Glass.

That probably tells you something about how I'm wired.

I've always felt like I was made for something bigger than just using the world as-is. An OS felt like the purest expression of that. It's not an app that solves one problem — it's the whole environment. The entire way a person experiences their machine. Build that, and you've built something close to a world.

So I kept building it. On paper, then Figma — version after version, design system after design system, across almost a decade. I loved designing it. I also spent a lot of those years wishing I could actually *use* it.

The gap between designing an OS and building one is enormous. Systems knowledge that takes years to develop. In late 2025 that finally changed — AI let me learn fast enough to close the gap myself. Nine years of accumulated design intent suddenly had somewhere to go.

# The Goal

Even though originally, it was just a way to kill some time, later on, I defined an actual goal for ZenOS.

It goes as follows:

**Make technology feel like magic. Get out of your way, give you real power, look good doing it.
Most OSes pick one or two of those. ZenOS is supposed to do all three.**

# The Design

## Before Figma

### **Glass circa 2016**

![Glass OS](/images/glassos.png)

Where it started. Drew this at 8 on actual paper. Already had the core instincts: taskbar, windows, apps.

### First (paper) ZenOS

![ZenOS paper](/images/zenos-paper.png)

It wasn't until 2020, though, until ZenOS got its current name.
Funnily enough, it wasn't actually called ZenOS but ZenOn instead.

### Inkscape experiments

Later on, I experimented with ZenOS on Inkscape... unfortunately, those designs were all lost.

## The Figma Era

### The first Figma ZenOS 

![ZenOS mid](/images/zenos-piss.png)

By this point it had a name & the vision was getting sharper, the gap to actually building it was still enormous.

### **Project Carbon / Neo**

![ZenOS Carbon](/images/n9-overview.png)

The most ambitious design era — infinite 2D canvas workspaces, advanced materials that maintain contrast against any background, collapsible UI elements. Figma struggled to render it in realtime.

### **NUDL 10 — Aerogel**

![Aerogel](/images/n10.png)

The final design vision as of writing this. Lightweight, almost like air. This is what ZenOS is supposed to feel like.

# Where It Is Now

ZenOS is built on NixOS and has its own DSL that compiles to Nix, its own package & module repository (ZenPkgs), and a custom installer. It's in alpha — the bones exist, the surfaces are still rough.

The roadmap is honest:

- **Beta** — DSL-wrapped NixOS, polished installer, a handful of custom options. A real usable system.
- **1.0.0** — Full GNOME desktop, app suite, module system, categorized packages. The complete experience.
- **2.0.0/3.0.0** — Custom DE. Genuinely far off, but it's where the Figma designs ultimately live.

![fastfetch](/images/fastfetch.png)

_The fastfetch looks good though._
