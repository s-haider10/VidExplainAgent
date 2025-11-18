# Human Evaluation Form for VidExplainAgent

## Instructions for Evaluators

Thank you for participating in this evaluation study! You will be evaluating AI-generated explanations from our video question-answering system designed for Blind and Low Vision (BLV) learners.

### Your Task

For each question-answer pair, you will rate the system's answer on **four dimensions** using a **5-point Likert scale** (1 = Strongly Disagree, 5 = Strongly Agree).

### Rating Dimensions

#### 1. Helpfulness (1-5)

**Statement:** "This answer helps me understand the video content."

- Does the answer provide useful information?
- Would this help a learner understand the topic?
- Is the information actionable?

#### 2. Clarity (1-5)

**Statement:** "The explanation is easy to understand."

- Is the language clear and accessible?
- Is the explanation well-structured?
- Are complex concepts explained appropriately?

#### 3. Completeness (1-5)

**Statement:** "The answer fully addresses the question."

- Does it answer all parts of the question?
- Is important information missing?
- Is there sufficient detail?

#### 4. Accessibility (1-5)

**Statement:** "A Blind or Low Vision user can follow this explanation."

- Are visual elements adequately described?
- Can the content be understood without seeing the video?
- Is spatial and visual information conveyed clearly?

### Rating Scale

| Score | Interpretation    |
| ----- | ----------------- |
| 1     | Strongly Disagree |
| 2     | Disagree          |
| 3     | Neutral           |
| 4     | Agree             |
| 5     | Strongly Agree    |

### Additional Guidelines

- **Be honest and objective** in your ratings
- **Consider the target audience**: BLV learners in STEM
- **Focus on content quality**, not personal preferences
- **Provide comments** when you give very low (1-2) or very high (5) scores
- **Take breaks** if needed - evaluation can be cognitively demanding

### Time Estimate

- Approximately 3-5 minutes per question
- Total time: ~30-60 minutes for 10-15 questions

### Example Evaluation

**Question:** "What is shown on the whiteboard at 1:15?"

**System Answer:** "At 1:15, the whiteboard displays a coordinate plane with x and y axes. A red parabola is drawn representing y = x², opening upward with its vertex at the origin."

**Your Ratings:**

- Helpfulness: 5 (Directly answers what is visible)
- Clarity: 5 (Clear, structured description)
- Completeness: 4 (Could mention axis labels)
- Accessibility: 5 (Excellent spatial description for BLV users)

**Comments:** "Great spatial description, though mentioning the axis scale would make it perfect."

---

## Evaluation Form

Please complete the CSV file provided with the following columns:

- `question_id`: (Pre-filled)
- `question`: (Pre-filled)
- `system_answer`: (Pre-filled)
- `helpfulness_score`: Your rating (1-5)
- `clarity_score`: Your rating (1-5)
- `completeness_score`: Your rating (1-5)
- `accessibility_score`: Your rating (1-5)
- `comments`: Optional text feedback

---

## Contact Information

If you have questions about the evaluation process, please contact: [Your Contact Info]

Thank you for your valuable contribution to making educational content more accessible!
