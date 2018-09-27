# gd2score

A tool to automatically create an SVG Allen Scorecard from [XML](http://gd2.mlb.com/components/game/mlb/) play by play data.

Read Dave Allen's description of this [new scoring method](http://baseballanalysts.com/archives/2010/02/another_attempt.php) and see a few more interesting game [examples](http://baseballanalysts.com/archives/2010/04/looking_at_some_1.php).

## XML Parsing and Enhancement
The game XML and player XML pages are parsed into Python objects. The resulting game object is then enhanced in various ways to add information essential to creating the scorecard. Most of the extra enhancements are necessary due to shortcomings in the raw XML.

Runner tags appear for the following reasons only, each of which use empty `end` tags to represent different things:
 * Advancement: `<runner start="" end="2B"/>` or `<runner start="2B" end="" score="T"/>`
 * Making an out: `<runner start="1B" end=""/>`
 * Stranded at the end of a half inning: `<runner start="1B" end=""/>`
 * Represent a pinch runner swap (only sporadically): `<runner start="2B" end=""/>` and `<runner start="" end="2B"/>`

Runner tags are not present within an at bat to represent a runner holding on a base. Ex: The batter strikes out with runners on or a runner holds at third on a groundout to first.

The following enhancements are made before drawing the SVG scorecard:
1. Pinch runner swaps, when present, are detected and removed. These unhelpful runner tags would otherwise be indistinguishable from normal runner tags.
2. Runners created with empty `end=""` tags are updated with the base where the out occurred or the runner was stranded. Runners scoring on a play are easily updated due to the `score="T"` attribute.
3. Runners are added to represent holding on a base.
4. Runners who reach base and eventually score have a flag added to each part of their advancement to indicate the run scoring.
5. A scoring code is added to represent the result of the atbat: G6, F8, P5, K, W, etc.
