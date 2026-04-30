---
name: api-availability
description: Use when the user mentions a specific iOS, iPadOS, macOS, visionOS, watchOS, tvOS, or Mac Catalyst version, references @available or #available or #unavailable, asks about minimum deployment targets, asks if an API is back-deployable, or asks whether an Apple API is deprecated, removed, or replaced.
---

# api-availability

Apple APIs gate strongly on platform version, and platform version data is exactly where Claude's training-data memory is least reliable. Without forced verification, you will confidently state wrong "since iOS X" strings, miss deprecations, and recommend APIs that don't exist on the user's deployment target.

## When to use

- User mentions a specific iOS, iPadOS, macOS, visionOS, watchOS, tvOS, or Mac Catalyst version
- User writes `@available(...)`, `#available(...)`, or `#unavailable`
- User asks about back-deployment or `if #available` fallback patterns
- User asks if an API is deprecated, removed, or has a replacement
- User mentions their app's minimum deployment target
- User asks "is this in iOS 18" / "did macOS Sequoia add X" / "when was Y introduced"
- User asks if a feature is in beta or final

## How to use

1. Search via `search_apple_docs` for the symbol in question
2. Call `read_apple_doc` on the highest-ranked result
3. Read the YAML frontmatter `platforms` field. It looks like:

   ```yaml
   platforms:
     - name: iOS
       since: '17.0'
     - name: macOS
       since: '14.0'
       deprecated: '15.0'
     - name: visionOS
       since: '1.0'
       beta: true
   ```

4. Cite the EXACT `since` string. Do not paraphrase. "Available since iOS 17.0" is correct; "iOS 17 and later" is sloppy.
5. If the API is unavailable on the user's deployment target:
   - Search for back-deployable alternatives or pre-version equivalents
   - Suggest an `if #available(iOS 17.0, *)` fallback pattern with a graceful pre-iOS-17 path
   - Do not pretend it is available
6. If the API is deprecated, name the replacement explicitly and check the replacement's own platforms.

## What NOT to do

- Never assert availability without reading the `platforms` field. Your training data is wrong about more than you think.
- Don't paraphrase the version. Quote it exactly so the user can search Apple's docs themselves.
- Don't suggest a deprecated API without flagging the replacement and checking that the replacement is itself available on the user's deployment target.
- Don't ignore beta flags. If `beta: true`, tell the user this is not stable yet.

## Red flags that you are about to violate the skill

- About to type a version number you remember from training data, without having opened the doc page
- About to say "I think this was added in..." without verification
- About to recommend an API based on its name alone, without checking platforms
- Skipping the lookup because the user asked a "simple" version question

All of these mean: search, read, then answer.
