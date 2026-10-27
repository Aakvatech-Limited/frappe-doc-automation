# End-to-end usage

The automated pipeline runs outside Frappe. No bench installation is required.

```bash
pip install -e '.[test,browser,site]'
frappe-docs pipeline --repo /work/av_rsvp --output ./generated --dry-run
frappe-docs pipeline --repo /work/av_rsvp --output ./generated
```

For screenshots install Chromium with `python -m playwright install chromium`, then provide a config based on `examples/pipeline.example.json`. Each role needs a saved Playwright authentication state from a sanitized staging site; store it outside the repository.

```bash
frappe-docs pipeline --repo /work/av_rsvp --output ./generated --config pipeline.json
```

Use `--ai` with `OPENAI_API_KEY` set to generate an **editorial draft** from static metadata. Review manually; it does not verify on-screen controls. This sends metadata to the OpenAI API.

Use `--pr` only after authenticating `gh` and configuring `target_repo`. It creates a draft documentation change as a PR, not an automatic merge.

Preview documentation with `mkdocs serve -f site/mkdocs.yml` after copying generated Markdown to `site/docs`.

Limitations: routes are inferred from metadata and may not exist on a running site. Form record screenshots require an explicit safe record selection strategy, which is not included. Always inspect generated images for sensitive data.
