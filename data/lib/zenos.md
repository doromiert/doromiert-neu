---

title: ZenOS
icon: zenos
tags: Operating Systems, Negative Zero, Software, Design

---

# The beginning
ZenOS is a really old project of mine, depending on how you count it, it started in 2016 (back then known as Glass OS) or 2020 (finally called ZenOS)

But the issue was always that it was first just a design on paper (yes, actual paper) or on Figma.

But since late 2025, I started actually putting together ZenOS the software, an actual operating system based on NixOS.

## What did it look like on paper, then?
![Glass OS](/images/glassos.png)

This was Glass. My first ever piece of UI design, back when i was only 8(!), bored in świetlica (which is like a daycare inside of an elementary school).

It was actually originally inspired by Windows and Ubuntu (which is where the orange accent color and name come from)

Later on, it went through so many iterations I don't think it makes sense to list them all here (and, anyways, looking for all of them will be tedious as all hell.)

## The Figma era

### V1: under construction
![ZenOS 1](/images/zenos-piss.png)

This is what the first Figma edition of ZenOS looked like. Very dark, very yellow.

But it had a few elements that eventually became the ZenOS UX staples:

1. dynamic app icons: my response to Apple's dynamic island
2. notification + widget side view
3. the window's top bar getting merged into the Action Center (which is the fancy name for the system top bar)

but of course, i eventually got bored with how that version of ZenOS looked so I designed a 

### V2: monochrome
![ZenOS 2](/images/zenos-mono.png)

This version of ZenOS had basically no color, not much has changed since V1 other than styling.

### V3: NUDL
![ZenOS 3](/images/zenos-n4.png)

Now this is where it gets interesting. This is the first ZenOS version using the Negative Zero Universal Design Language, shortened to NUDL (purposely skipped Z so that it's pronounced as noodle)... version 4.

Yep, NUDL v1-v3 had no desktop version whatsoever, only a mobile one.

Well, not exactly, there were *some* desktop apps but there wasn't an actual desktop mode in NUDL 1. 

It was the first ZenOS version that didnt have detached window buttons too.

### V4: NUDL 5
![NUDL 5](/images/nudl-5.png)

This version was mainly just a continuation & polish of the NUDL 4 version of ZenOS, not much has changed.

It was also the first ZenOS version that had designs for desktop, mobile and XR.

### V5: ZenOS 4.0/NUDL 5.1
![ZenOS 4](/images/zenos-4.png)

Minor refinements to the NUDL 5.0 version, most of the work was actually componentizing the design system & building more screens.

### V6: ZenOS 5.0/NUDL 6.0
![ZenOS 5](/images/zenos-5.png)

This was the biggest departure from the NUDL formula design-wise.

It removed the background behind every element idea.

That didn't last long though.

### V7: ZenOS 6.0/NUDL 6.1
![ZenOS 6](/images/zenos-6.png)

This was the ZenOS version with the most screens. 
It also introduced progressive blur into the UI.

### V8: NUDL 7 & 8

These two versions didn't really do much if I'm being honest.
They were more just something to do to keep my mind occupied when I was bored.

### V9: NUDL 9 AKA Project Carbon
![ZenOS 9 overview](/images/n9-overview.png)
![ZenOS 9 views](/images/n9-views.png)

This version entirely reimagined the desktop as an infinite 2D canvas where each workspace (here called view) is just a purposely cut off section of that canvas that you can focus on.
It was also the version that introduced what I call advanced materials, which are materials that are designed to keep maximum contrast and color passthrough no matter the background.

The UI was so complex Figma struggled to render it in real time.

### V10: NUDL 9.1 AKA Project Neo
![ZenOS 10 overview](/images/neo-overview.png)
![Chameleon](/images/chameleon.png)

This version took what was great about Project Carbon and improved it.
It introduced Cameleon, a material that automatically decides whether it should be black or white depending on the background to maintain optimal contrast.
This version also introduced collapsible elements; elements that can shrink down into just lines to indidate their existence without taking up too much space, which is especially useful on mobile platforms.

It also turned the app list into a 3x∞ grid.

### V11: NUDL 10 AKA Project Aerogel/Lychee
![Aerogel](/images/n10.png)

The name of the game for NUDL 10 was that it's supposed to feel lightweight, like air.
It's also supposed to be the final NUDL version.

# Real software

Now that we've gone over how it looked on paper and how it looked on figma, we can finally get into the real software side of things.

ZenOS N started off as just NixOS dotfiles, but later on I realized that making it a full-on operating system will require more than just that.
