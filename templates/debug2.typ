#set page(margin: (x: 1.5cm, y: 1.5cm), paper: "a4")

#text(weight: "bold", size: 14pt)[Test: Grid WITH block() wrappers]
#v(0.5em)

#grid(
  columns: (11.16cm, 0.54cm, 6.3cm),
  gutter: 0pt,
  block(width: 11.16cm)[
    LEFT COLUMN WITH BLOCK WRAPPER
    Multiple lines
    More content
  ],
  [],
  block(width: 6.3cm)[
    RIGHT COLUMN WITH BLOCK WRAPPER
    Multiple lines
    More content
  ]
)
