// ============================================================
// resume_template.typ - FINAL REBUILD with proper #grid()
// Data is injected via resume_data.json (written by tailor.py)
// Compile with: typst compile --root . templates/resume_template.typ output/tailored_cv.pdf
// ============================================================

// --- Data ---
#let data = json("resume_data.json")

// --- Colors ---
#let navy = rgb("#1a3a5c")
#let teal = rgb("#1a7a7a")

// --- Page Setup ---
#set page(margin: (top: 0.8cm, bottom: 1.5cm, x: 1.2cm), paper: "a4")
#set text(font: "New Computer Modern", size: 9pt, fill: rgb("#222222"))
#set par(leading: 0.55em)

// Suppress default heading styles
#show heading: it => it.body


// ============================================================
// HELPER FUNCTIONS
// ============================================================

#let section-heading(title) = [
  #text(size: 13pt, weight: "bold", fill: navy)[#title]
  #v(-6pt)
  #line(length: 95%, stroke: 1pt + teal)
  #v(2pt)
]

#let section-heading-sm(title) = [
  #text(size: 12pt, weight: "bold", fill: navy)[#title]
  #v(-6pt)
  #line(length: 95%, stroke: 1pt + teal)
  #v(1pt)
]

#let experience-entry(dates, location, role, role-color, bullets) = [
  #grid(
    columns: (2.2cm, 1fr),
    gutter: 1.5pt,
    align(left)[
      #text(size: 9pt, fill: rgb("#555555"))[#dates #linebreak() #location]
    ],
    align(left)[
      #text(weight: "bold", fill: role-color)[● #role]
      #pad(left: 0.4cm)[
        #for bullet in bullets [
          - #bullet
        ]
      ]
    ]
  )
  #v(3pt)
]

#let education-entry(degree, university, location, dates, logo) = [
  #grid(
    columns: (1fr, 1.2cm),
    gutter: 6pt,
    align(left)[
      #text(weight: "bold")[#degree]
      #linebreak()
      #text(fill: rgb("#555555"))[#university]
      #linebreak()
      #text(fill: rgb("#555555"))[#location]
      #linebreak()
      #text(size: 9pt)[#dates]
    ],
    align(right + horizon)[
      #if logo != "" [
        #image(logo, width: 1.1cm)
      ]
    ]
  )
  #v(2pt)
]


// ============================================================
// ZONE 1: FULL-WIDTH HEADER
// ============================================================

#let c = data.contact

#grid(
  columns: (14cm, 4cm),
  gutter: 8pt,
  align(left)[
    #v(25pt)
    #text(size: 30pt, weight: "bold", fill: navy)[#c.name]
    #v(0pt)
    #grid(
      columns: (4cm, 3cm, 3cm, 1fr),
      gutter: 3pt,
      align(left)[✉ #link("mailto:" + c.email)[#text(size: 9pt)[#c.email]]],
      align(left)[☎ #text(size: 9pt)[#c.phone]],
      align(left)[@ #link("https://" + c.linkedin)[#text(size: 9pt)[#c.linkedin_slug]]],
      align(left)[◆ #text(size: 9pt)[#c.nationality]],
    )
  ],
  align(right)[
    #if c.keys().contains("photo_path") and c.photo_path != "" [
      #box(
        width: 3.2cm,
        height: 3.2cm,
        clip: true,
        image(c.photo_path, width: 3.2cm, height: 3.2cm, fit: "cover"),
        stroke: none,
        radius: 50%,
      )
    ]
  ]
)

#v(1pt)
#line(length: 100%, stroke: 0.5pt + rgb("#cccccc"))
#v(1pt)


// ============================================================
// ZONE 2: TWO-COLUMN BODY
// Using explicit grid with NO block() wrappers
// Left: 11.8cm (Professional + Extracurricular)
// Gap: 0.54cm
// Right: 6.5cm (Summary + Education + Languages + Skills + Awards)
// ============================================================

#grid(
  columns: (11.8cm, 0.54cm, 6.5cm),
  gutter: 0pt,

  // === LEFT COLUMN CONTENT (no block wrapper!) ===
  [
    #section-heading("Professional Experience")
    #for job in data.experience [
      #grid(
        columns: (1.2cm, 1fr),
        gutter: 5pt,
        align(left)[
          #if job.keys().contains("logo_path") and job.logo_path != "" [
            #image(job.logo_path, width: 1cm)
          ]
        ],
        align(left)[
          #text(weight: "bold")[#job.company]
          #linebreak()
          #text(style: "italic", fill: rgb("#555555"), size: 9pt)[#job.description]
        ]
      )
      #v(1pt)
      #for role in job.roles [
        #experience-entry(role.dates, role.location, role.role, navy, role.bullets)
      ]
    ]
    
    #v(1pt)
    #section-heading("Extracurricular Experience")
    #for ex in data.extracurricular [
      #grid(
        columns: (2.2cm, 1fr),
        gutter: 1.5pt,
        align(left)[
          #text(size: 9pt, fill: rgb("#555555"))[#ex.dates #linebreak() #ex.location]
        ],
        align(left)[
          #text(weight: "bold")[#ex.event]
          #linebreak()
          #text(style: "italic", size: 9pt, fill: rgb("#555555"))[#ex.section]
          #linebreak()
          #text(weight: "bold", fill: navy)[● #ex.role]
          #pad(left: 0.4cm)[
            #for bullet in ex.bullets [
              - #bullet
            ]
          ]
        ]
      )
      #v(1pt)
    ]
  ],

  // === SPACER ===
  [],

  // === RIGHT COLUMN CONTENT (no block wrapper!) ===
  [
    #set text(size: 9pt)
    #section-heading-sm("Summary")
    #text(size: 9pt)[#data.tailored_summary]
    #v(4pt)

    #section-heading-sm("Education")
    #for ed in data.education [
      #education-entry(ed.degree, ed.university, ed.location, ed.dates, ed.at("logo_path", default: ""))
    ]

    #section-heading-sm("Languages")
    #for lang in data.languages [
      #text(weight: "bold")[#lang.name: ]
      #text[#lang.level]
      #linebreak()
    ]
    #v(4pt)

    #section-heading-sm("Skills")
    #for (category, skills) in data.skills.pairs() [
      #text(weight: "bold")[#category]
      #linebreak()
      #text(size: 8pt)[#skills]
      #v(2pt)
    ]

    #if data.keys().contains("awards") and data.awards.len() > 0 [
      #v(4pt)
      #section-heading-sm("Awards & Scholarships")
      #for award in data.awards [
        - #award
      ]
    ]
  ]
)
