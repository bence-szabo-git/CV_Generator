#set page(margin: (x: 1.5cm, y: 1.5cm), paper: "a4")

// Test 1: Simple two-column grid without blocks
#text(weight: "bold", size: 14pt)[TEST 1: Simple Grid]
#v(0.5em)

#grid(
  columns: (11cm, 7cm),
  gutter: 0pt,
  [LEFT COLUMN - This should appear on the left side of the page],
  [RIGHT COLUMN - This should appear on the right side]
)

#v(2em)

// Test 2: Grid with more content
#text(weight: "bold", size: 14pt)[TEST 2: Grid with Content]
#v(0.5em)

#grid(
  columns: (11cm, 7cm),
  gutter: 0pt,
  [
    LEFT:
    - Line 1
    - Line 2
    - Line 3
    - Line 4
    - Line 5
  ],
  [
    RIGHT:
    - Item A
    - Item B
    - Item C
    - Item D
  ]
)

#v(2em)

// Test 3: Three-column grid like the resume uses
#text(weight: "bold", size: 14pt)[TEST 3: Three-Column Grid (like resume)]
#v(0.5em)

#grid(
  columns: (11.16cm, 0.54cm, 6.3cm),
  gutter: 0pt,
  [LEFT CONTENT],
  [],
  [RIGHT CONTENT]
)
