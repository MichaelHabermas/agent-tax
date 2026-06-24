# BUGS AND MITIGATIONS

## Bugs

- Public Render URL was still serving the old placeholder app because the working local changes had not been committed and pushed.
- W-2 extraction currently supports text-readable PDFs, not scanned/blurry image-only W-2s.
- Scope is intentionally narrow: one W-2, federal 1040, standard deduction, no other income, no itemized deductions, no credits, no e-filing.

## Mitigations

- Commit and push this working version to the GitHub mirror Render deploys from, then smoke-test the live URL.
- Keep the supplied `assets/w2_filled_sample_2025.pdf` as the judge/demo fixture; failed extraction returns a clear validation error instead of producing a fake return.
- Guardrails block out-of-scope paths and the trace panel shows the block. The app states it is an educational prototype and not tax advice.
