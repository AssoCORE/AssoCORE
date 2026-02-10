# Documentation Structure

This document outlines the organization of AssoCORE documentation.

## Folder Structure

```sh
docs/src/content/docs/
├── index.mdx                      # Homepage
├── getting-started/               # Getting Started
│   ├── index.md                   # Overview
│   ├── introduction.md            # What is AssoCORE?
│   ├── installation.md            # Installation guide
│   └── quickstart.md              # Quick start tutorial
│
├── guides/                        # Guides
│   ├── index.md                   # Guides overview
│   ├── tutorials/                 # Step-by-step tutorials
│   │   └── ...
│   └── how-to/                    # Task-oriented guides
│       └── ...
│
├── reference/                     # Reference
│   ├── index.md                   # Reference overview
│   ├── api/                       # API documentation
│   │   └── ...
│   └── configuration/             # Configuration docs
│       └── ...
│
├── architecture/                  # Architecture
│   ├── index.md                   # Architecture overview
│   ├── system-design.md           # System architecture
│   ├── data-models.md             # Data structures
│   ├── security.md                # Security design
│   └── tech-stack.md              # Technologies used
│
├── pocs/                          # Proof of Concepts
│   ├── index.md                   # POCs overview
│   └── [poc-name].md              # Individual POC documents
│
├── studies/                       # Research Studies
│   ├── index.md                   # Studies overview
│   ├── comparative/               # Comparative studies
│   │   ├── index.md               # Comparative studies overview
│   │   └── [study-name].md        # Individual comparative studies
│   └── field/                     # Field studies
│       ├── index.md               # Field studies overview
│       └── [study-name].md        # Individual field studies
│
├── case-studies/                  # Case Studies
│   ├── index.md                   # Case studies overview
│   └── [association-name].md      # Individual case studies
│
└── contributing/                  # Contributing
    ├── index.md                   # Contributing guide
    ├── code-guidelines.md         # Code standards
    └── documentation-guide.md     # Doc standards
```

## Section Purposes

### Getting Started

**Target Audience:** New users
**Goal:** Help users understand and start using AssoCORE quickly
**Content Type:** Introduction, installation, quick wins

### Guides

**Target Audience:** Users learning to use AssoCORE
**Goal:** Teach features and best practices
**Content Type:**

- **Tutorials:** Learning-oriented, step-by-step lessons
- **How-To Guides:** Task-oriented, problem-solving guides

### Reference

**Target Audience:** Developers and integrators
**Goal:** Provide technical specifications and API docs
**Content Type:** API docs, configuration options, technical specs

### Architecture

**Target Audience:** Developers and technical stakeholders
**Goal:** Explain technical design and implementation
**Content Type:** System design, patterns, technology choices

### Proof of Concepts (POCs)

**Target Audience:** Product team and stakeholders
**Goal:** Document experimental features and prototypes
**Content Type:** POC descriptions, validation results, decisions
**When to use:** Testing new ideas before full implementation

### Studies

**Target Audience:** Product team, researchers, stakeholders
**Goal:** Share research insights and analysis
**Content Type:**

#### Comparative Studies

- Compare different tools/approaches
- Analyze pros/cons
- Provide recommendations
- Example: "Association Management Platform Comparison 2026"

#### Field Studies

- Real-world research with associations
- User observation and interviews
- Usage patterns and pain points
- Impact measurement
- Example: "Member Engagement Patterns in Small Nonprofits"

### Case Studies

**Target Audience:** Prospects and users seeking inspiration
**Goal:** Showcase real success stories
**Content Type:** Association profiles, challenges, solutions, results
**Format:** Problem → Solution → Impact

### Contributing

**Target Audience:** Contributors
**Goal:** Guide people in contributing to AssoCORE
**Content Type:** Contribution guidelines, code standards, processes

## Content Guidelines

### For Studies

**Comparative Studies should include:**

- Clear methodology
- Consistent evaluation criteria
- Objective analysis
- Data sources
- Date of study (important for relevance)

**Field Studies should include:**

- Association context (size, type, location)
- Study methodology
- Key findings
- Quotes/testimonials (with permission)
- Actionable insights
- Privacy considerations (anonymize if needed)

### For POCs

Each POC document should answer:

- What problem does this solve?
- What was built?
- What was learned?
- What's the next step? (integrate / iterate / archive)
- Date and team members involved

### For Case Studies

Each case study should include:

- Association background
- The challenge
- How they used AssoCORE
- Quantifiable results
- Testimonials
- Key takeaways

## Naming Conventions

- Use lowercase with hyphens: `member-management.md`
- Be descriptive: `email-automation-setup.md` not `setup.md`
- Date studies if time-sensitive: `2026-crm-comparison.md`
- Use association names for case studies: `green-earth-nonprofit.md`

## Writing Style

- **Getting Started & Guides:** Friendly, encouraging, tutorial-style
- **Reference:** Technical, precise, concise
- **Architecture:** Technical but accessible, explain the "why"
- **Studies:** Academic/professional, data-driven, objective
- **Case Studies:** Storytelling, inspiring, results-focused
- **POCs:** Experimental, open to exploration, hypothesis-driven

## Maintenance

- Review field studies annually for relevance
- Update comparative studies when market changes
- Archive old POCs once decisions are made
- Keep case studies updated with current product state
- Update getting started guide with each major release
