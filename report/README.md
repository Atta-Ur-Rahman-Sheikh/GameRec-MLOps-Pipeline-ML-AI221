# IEEEtran report

Build dependencies: a full LaTeX install with `IEEEtran.cls` (TeX Live / MiKTeX).

```bash
cd report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Source structure:

- `main.tex` — document class + `\input` sections
- `sections/*.tex` — paper body + extended ML appendix
- `refs.bib` — BibTeX entries (expand as needed)
- `figures/` — drop exported notebook PNG/PDF plots here

The extended appendix `sections/supplement_ml_extended.tex` is intentionally long for the team to mine prose and viva notes; trim before camera-ready if page limits apply.
