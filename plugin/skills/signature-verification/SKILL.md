---
name: signature-verification
description: Use before writing any line of Apple platform code that calls a framework symbol you have not just looked up in this conversation. Triggered when about to assert that a specific Apple API method, initializer, property, protocol requirement, or enum case exists with a specific signature.
---

# signature-verification

Hallucinated method signatures are the single biggest reason iOS and macOS developers distrust AI-generated code. Without verification you will confidently produce:

- Method names that do not exist
- Wrong parameter labels (`init(name:)` when the real one is `init(named:)`)
- Wrong return types
- APIs from one framework attributed to another (claiming a SwiftUI modifier that is actually UIKit-only)
- Old completion-handler signatures for APIs that are now async-only
- Removed or renamed symbols that your training data still remembers

The user cannot tell from the generated code that any of this is wrong. They run it, the build fails or crashes at runtime, and trust collapses. The fix is one rule: do not write Apple framework code from memory; verify first.

## When to use

Before writing any of:

- A method call on an Apple framework type (`tableView.dequeueReusableCell...`, `view.modifier(...)`)
- An initializer of an Apple type (`URLSession(configuration:)`, `TabView(selection:content:)`)
- A protocol conformance that has required methods (`UITableViewDataSource`, `View`, `Identifiable`)
- A property access you are not 100% certain exists with that exact name and type
- An enum case from an Apple type
- A SwiftUI view modifier or environment value
- An async / throwing version of an API where you are not sure of the variant

## How to use

1. Search via `search_apple_docs` for the type and method name. Filter by framework when known.
2. Call `read_apple_doc` on the highest-ranked result.
3. Read the declaration block under the frontmatter. It is the first fenced code block. That is the canonical signature.
4. Match the EXACT signature in your generated code:
   - Parameter labels (external and internal)
   - Parameter types (including optionality)
   - Return type (including optionality and throws/async)
   - Generic constraints if any
5. If your originally-imagined signature differs from what the docs show, use the verified one. Do not "split the difference."
6. If you cannot find the symbol after a focused search, tell the user "I could not verify this exists in the indexed Apple docs" and propose alternatives instead of inventing one.

## What NOT to do

- Never write Apple framework code from memory for a symbol you have not looked up in this session
- Don't paraphrase signatures from search snippets — they are summaries, not declarations. Read the full doc page.
- If you cannot find a symbol, do not invent one to satisfy the user's request. Say so explicitly.
- Don't trust your memory of Swift evolution. APIs are renamed and deprecated frequently.
- Don't skip verification because the API "feels" obvious. The obvious-feeling ones are exactly where parameter labels get hallucinated.

## Red flags that you are about to violate the skill

- About to type a method call without having read the doc page in this conversation
- About to fill in parameter labels from memory because they "feel right"
- About to use a completion-handler version of an API without checking if there is an async version
- About to add a SwiftUI modifier you have not verified exists
- "I'm pretty sure the signature is..." — pretty sure is not verified

All of these mean: search, read the declaration, then write the code with the verified signature.

## One verified call beats ten plausible ones

The user does not need volume. They need correctness. A short answer with three verified API calls beats a long answer with ten plausible-but-hallucinated ones, every time.
