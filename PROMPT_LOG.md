# AI Prompt Log

The assessment asks for an initial AI prompt, one issue observed in an initial chart draft, and a follow-up prompt.

## Initial chart prompt
"Write a Python script that reads the device summary JSON and creates a Matplotlib bar chart comparing average temperature by device. Include a title, axis labels, readable category labels, and save the chart as a PNG."

## Issue identified during review
The first chart draft did not provide enough spacing around the plot and did not make individual bar values easy to compare. Empty input also needed an explicit visual state.

## Follow-up chart prompt
"Improve the chart layout to prevent crowded labels. Use a wider figure, tight_layout, value labels above bars, axis labels, a subtle y-axis grid, and a clear message when the JSON contains no devices. Save the result as a PNG."

## Additional AI assistance
AI assistance was also used to plan and review optional extensions beyond the minimum assessment requirements: row validation, additional descriptive statistics, configurable thresholds, logging, health labels, and a second chart. The implementation was reviewed and tested. The Section 1 cleaning function should be understood and independently explained by the candidate because the assessment specifies that Section 1 is to be completed without AI assistance.
