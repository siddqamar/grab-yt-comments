# Evaluation Guide for YouTube Comment Classifier

This guide ensures **consistent human labeling** when building the golden dataset. Consistent labels are the foundation for measuring and improving the small local LLM (LFM2.5-350M).

The classifier assigns **exactly one** label per comment. Your job as labeler is to pick the single best bucket that a creator or product team would find most actionable.

---

## The 7 Labels (Canonical)

Use these exact strings in the gold dataset:

1. `appreciation`
2. `humor`
3. `questions`
4. `criticism`
5. `personal experience`
6. `feedback`
7. `spam`

### Detailed Definitions + Examples

**appreciation**
- Praise, thanks, agreement, encouragement, or saying the content helped.
- Positive, low-information reactions.
- Examples:
  - "Great video! Thank you so much ❤️"
  - "This is exactly what I needed today"
  - "Loved it, keep it up!"
  - "You really deserve likes such well informative channel"
- NOT: A full story about the user's life (→ personal experience), or a suggestion (→ feedback).

**humor**
- Jokes, memes, playful remarks, or light sarcasm meant mainly to entertain.
- Short laughs, puns, "lol" style when clearly joking.
- Examples:
  - "This is me at 3am watching this instead of sleeping 😂"
  - "Plot twist: the real lesson is don't watch this at work"
- Edge: Sarcastic "amazing..." that is clearly negative → criticism.

**questions**
- Asks for information, help, clarification, a tutorial, an example, or a future topic.
- Explicit or strong implied requests.
- Examples:
  - "Can you make a video about office politics?"
  - "Which of the 10 lessons resonated most?"
  - "How do you handle this when the manager is the problem?"
- "Please explain X" counts even if polite.

**criticism**
- Complains, disagrees, reports a problem, expresses confusion, or gives negative judgment.
- Tone is negative or points out flaws.
- Examples:
  - "This is completely wrong for my industry"
  - "You missed the most important part..."
  - "Not all managers have favorites..." (defensive pushback)
- Includes "I don't agree" + reasoning.

**personal experience**
- Shares a first-person story, outcome, use case, or lived experience.
- "I did X and Y happened", "In my 10 years...", "As a woman from..."
- Strong signal: "I", "my", "we" + concrete past/present outcome.
- Examples:
  - "I work in industrial automation and the non technical manager part really hit close to home"
  - "after 20 years in tech... my sincere advice..."
  - "I’m 33 now female from Afghanistan and worked 10yrs but never promoted"
- May contain positive/negative feelings, but the core is the personal narrative.

**feedback**
- Gives a suggestion, feature request, constructive advice, or improvement idea.
- Actionable for the creator.
- Examples:
  - "Please make a video about office politics because..."
  - "You should also read 'The Effective Executive'..."
  - "Would love some more insights into how to transition..."
- Overlap rule: If it contains a clear "do this" or "next video on", prefer feedback over personal experience.

**spam**
- Clear scam, bot text, unrelated promotion, repeated junk, suspicious link, fake giveaway, or self-promotion.
- Off-topic affiliate links with no engagement.
- Examples:
  - Long promo with discount code + link at the top
  - "Make money fast join my group"
  - Copied comments or obvious SEO spam
- Short self-promo in context of the topic may be "feedback" — be conservative.

---

## Decision Rules & Priority Order (for Ambiguous Cases)

When a comment touches multiple categories, use this priority:

1. **spam** — if there's any clear spam signal (link + promo + no substance) → spam.
2. **questions** — if it ends with a clear ask or "can you" / "how do".
3. **personal experience** — heavy "I/my story" + concrete outcome. Even if thankful.
4. **feedback** — explicit suggestion or "you should make a video about".
5. **criticism** — dominant negative tone or disagreement.
6. **humor** — clearly playful / joke primary purpose.
7. **appreciation** — generic positive reaction.

Mixed examples:
- "Loved the video! This helped me a lot in my first year as a manager after I switched careers." → `personal experience` (strong story).
- "Great tips. Can you cover corporate politics next? I failed for years because of it." → `questions` + `feedback` → lean `questions` (explicit ask) or `feedback` if suggestion is stronger. Default to `feedback` when "make a video" language.
- "lol this is so true" → `humor` or `appreciation`. Choose `humor` if "lol" or emoji joke.

When in doubt:
- Read the whole comment.
- Ask: "What would a creator most want to know or act on?"
- Write a short note in the labeler.

---

## Annotation Workflow Tips

- Use the interactive labeler script (`interactive_label.py`).
- Read the full text (use "full" option if truncated).
- Prefer exact match to definitions above over gut feel.
- Add `labeler_notes` for borderline cases — these become gold for prompt improvement.
- If you make a mistake, you can re-run the labeler on the same gold file later (it skips already labeled).
- After labeling 20+, re-label 5 random ones yourself and compare. Note disagreements.

---

## Sources of Labels

The definitions above are copied/adapted directly from the prompts inside `backend/classifier.py` (`_build_comment_payload` and `_build_batch_payload`) plus the `_normalize_label` aliases.

When the model is improved, the prompt text and this guide should stay in sync.

---

## Growing the Gold Set

- Start with 100–150 from the existing `backend/outputs/`.
- Add harder examples: very long comments, non-English fragments, heavy code, mixed signals.
- Every major prompt change should be validated against the full committed gold set.
- Never remove examples — append new ones.

Good luck — your labels will directly improve the quality of the classifier!
