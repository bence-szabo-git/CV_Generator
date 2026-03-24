// ============================================================
// resume_template.typ - REBUILT
// Data is injected via resume_data.json (written by tailor.py)
// Compile with: typst compile --root . templates/resume_template.typ output/tailored_cv.pdf
// ============================================================

// --- Data ---
#let data = json("resume_data.json")

// --- Colors ---
#let navy = rgb("#1a3a5c")
#let teal = rgb("#1a7a7a")

// --- Page Setup ---
#set page(margin: (x: 1.5cm, y: 1.5cm), paper: "a4")
#set text(font: "New Computer Modern", size: 10pt, fill: rgb("#222222"))
#set par(leading: 0.55em)

// Suppress default heading styles
#show heading: it => it.body


// ============================================================
// HELPER FUNCTIONS
// ============================================================

#let section-heading(title) = [
  #text(size: 13pt, weight: "bold", fill: navy)[#title]
  #v(-6pt)
  #line(length: 100%, stroke: 1pt + teal)
  #v(4pt)
]

#let experience-entry(dates, location, role, role-color, bullets) = [
  #grid(
    columns: (2.8cm, 1fr),
    gutter: 8pt,
    align(left)[
      #text(size: 8.5pt, fill: rgb("#555555"))[#dates #linebreak() #location]
    ],
    align(left)[
      #text(weight: "bold", fill: role-color)[● #role]
      #v(2pt)
      #for bullet in bullets [
        - #bullet
      ]
    ]
  )
  #v(4pt)
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
      #text(size: 8.5pt)[#dates]
    ],
    align(right)[
      #if logo != "" [
        #image(logo, width: 1.1cm)
      ]
    ]
  )
  #v(6pt)
]


// ============================================================
// ZONE 1: FULL-WIDTH HEADER
// ============================================================

#let c = data.contact

#grid(
  columns: (13cm, 5cm),
  gutter: 0pt,
  align(left)[
    #text(size: 28pt, weight: "bold", fill: navy)[#c.name]
    #v(6pt)
    #grid(
      columns: (6.5cm, 6.5cm),
      gutter: 4pt,
      [✉ #link("mailto:" + c.email)[#c.email]],
      [✆ #c.phone],
      [in #link("https://" + c.linkedin)[#c.linkedin]],
      [⊕ #c.nationality],
    )
  ],
  align(right)[
    #if c.keys().contains("photo_path") and c.photo_path != "" [
      #box(
        width: 3.5cm,
        height: 3.5cm,
        image(c.photo_path, width: 3.5cm, height: 3.5cm, fit: "cover")
      )
    ]
  ]
)

#v(8pt)
#line(length: 100%, stroke: 0.5pt + rgb("#cccccc"))
#v(10pt)


// ============================================================
// ZONE 2: TWO-COLUMN BODY
// Using absolute widths: Left 11.16cm, Gap 0.54cm, Right 6.3cm
// NO block() wrappers — use raw [] content cells instead
// ============================================================

#grid(
  columns: (11.16cm, 0.54cm, 6.3cm),
  gutter: 0pt,

  // ===== LEFT COLUMN (Professional + Extracurricular) =====
  [
    #section-heading("Professional Experience")

    #for job in data.experience [
      #grid(
        columns: (1.2cm, 1fr),
        gutter: 6pt,
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
      #v(4pt)
      #for role in job.roles [
        #experience-entry(
          role.dates,
          role.location,
          role.role,
          navy,
          role.bullets
        )
      ]
    ]

    #section-heading("Extracurricular Experience")

    #for ex in data.extracurricular [
      #grid(
        columns: (2.8cm, 1fr),
        gutter: 8pt,
        align(left)[
          #text(size: 8.5pt, fill: rgb("#555555"))[#ex.dates #linebreak() #ex.location]
        ],
        align(left)[
          #text(weight: "bold", fill: teal)[#ex.role]
          #linebreak()
          #text(weight: "bold")[#ex.event]
          #linebreak()
          #text(style: "italic", size: 9pt)[#ex.section]
          #v(2pt)
          #for bullet in ex.bullets [
            - #bullet
          ]
        ]
      )
      #v(6pt)
    ]
  ],

  // ===== GAP COLUMN =====
  [],

  // ===== RIGHT COLUMN (Education, Languages, Skills, Awards) =====
  [
    #section-heading("Summary")
    #text(size: 9.5pt)[#data.tailored_summary]
    #v(10pt)

    #section-heading("Education")
    #for ed in data.education [
      #education-entry(
        ed.degree,
        ed.university,
        ed.location,
        ed.dates,
        ed.at("logo_path", default: "")
      )
    ]

    #section-heading("Languages")
    #for lang in data.languages [
      #text(weight: "bold")[#lang.name: ]
      #text[#lang.level]
      #linebreak()
    ]
    #v(8pt)

    #section-heading("Skills")
    #for (category, skills) in data.skills.pairs() [
      #text(weight: "bold")[#category]
      #linebreak()
      #text(size: 9pt)[#skills]
      #v(4pt)
    ]

    #if data.keys().contains("awards") and data.awards.len() > 0 [
      #v(4pt)
      #section-heading("Awards & Scholarships")
      #for award in data.awards [
        - #award
      ]
    ]
  ]
)
