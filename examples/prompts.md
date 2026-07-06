# Cobsidian Prompt Examples

Use these prompts as starting points. Replace placeholder paths and topics with your own values.

## Basic Write

```text
Use Cobsidian to organize this material into my Obsidian vault.
Vault: /path/to/vault
Topic: <topic>

Search existing notes first, decide whether to create or append, add useful wiki links, and run validation.
```

## Dry Run Before Editing

```text
Use Cobsidian in dry-run mode.
Vault: /path/to/vault

Do not edit files yet. First report:
- target note
- create vs append decision
- duplicate risks
- suggested backlinks
- proposed Markdown outline
```

## Let The Agent Introduce Modes

```text
Use Cobsidian to organize this into my Obsidian vault.
I have not chosen a mode. Briefly introduce the available modes if the note shape is ambiguous, then ask me to choose or let you infer it.
```

## Learning Mode

```text
Use Cobsidian in learning mode.
Vault: /path/to/vault
Topic: <concept, course, paper, video, or article>

Write a durable learning note with core concepts, mental model, common mistakes, and related notes.
```

## Project Mode

```text
Use Cobsidian in project mode.
Vault: /path/to/vault
Project: <project name>

Summarize the project architecture, implementation evidence, risks, and next steps.
Search existing project notes before writing.
```

## Review Mode

```text
Use Cobsidian in review mode.
Vault: /path/to/vault
Event: <incident, failed run, debugging session, or experiment>

Write a review note with context, timeline, symptoms, root cause, fix, lessons, and next steps.
```

## Comparison Mode

```text
Use Cobsidian in comparison mode.
Vault: /path/to/vault
Options: <option A>, <option B>, <option C>

Create a concise comparison note with a short conclusion, comparison table, decision rules, and recommended use cases.
```

## Index Mode

```text
Use Cobsidian in index mode.
Vault: /path/to/vault
Topic: <topic area>

Build a hub note or learning path. Link existing notes, group them by theme, and list open questions.
```

## Daily Capture Mode

```text
Use Cobsidian in daily capture mode.
Vault: /path/to/vault

Save the following material as a short capture note. Keep it searchable, but do not over-polish it.
```

## Dissection Mode

```text
Use Cobsidian in dissection mode.
Vault: /path/to/vault
Object: <repo, framework, tool, prompt system, skill, or agent workflow>

Break down purpose, entry points, core flow, key files or components, reusable patterns, limits, and related notes.
```

## Backlink Cleanup

```text
Use Cobsidian to improve links in my vault.
Vault: /path/to/vault
Target note: <note path or title>

Suggest useful backlinks and wiki links. Do not add noisy keyword links.
Report links added, skipped, and missing targets.
```

## Duplicate Check

```text
Use Cobsidian to check duplicate notes.
Vault: /path/to/vault

Run duplicate detection, summarize exact or similar titles, and recommend merge/append actions before editing.
```

## Config-Aware Run

```text
Use Cobsidian and follow cobsidian.config.yml.

Organize the following material into the configured vault.
Respect naming, directory, safety, linking, and validation rules from the config.
```

## Config-Aware Dry Run

```text
Use Cobsidian and follow cobsidian.config.yml.
Do not write files yet.

Run a dry run and return JSON with:
- create/append decision
- duplicate risks
- suggested backlinks
- validation intent
- writes as an empty list
```
