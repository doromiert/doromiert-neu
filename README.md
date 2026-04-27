# doromiert.neg-zero.com

I didn't like my personal site

So i'm redoing it

In plain HTML, no js no nonsense like that, \<14kb

## how to run

aside from ofc visiting doromiert.neg-zero.com once it's done, just run nix run . and it'll open it locally

yes, you NEED nix

## content system

- lib/slug.md        → card in lib section + /lib/slug.html article page
- blog/YYYY-MM-DD.md → latest post inline in blog + /blog/slug.html + /blog/index.html
- devices/slug.md    → categorized row in devices + /devices/slug.html article page
- music/slug.md      → categorized row in music + /music/slug.html article page
- music/_now.txt     → two lines: song title / artist  (optional, shown in music)

Frontmatter keys (all optional):
- title, subtitle, icon, tags (comma-sep), category (devices/music), date (blog),
- url (lib: external link overrides generated article page)
