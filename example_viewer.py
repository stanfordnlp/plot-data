"""
Simple script for visualizing training examples.

Examples are grouped by the targetFormula.

Usage:
    $ python example_viewer.py -d /path/to/data/turk_overnight_2k.jsonl -o /some/output/dir
"""
import argparse
import json
import os
from collections import defaultdict

from os.path import join

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--data_path')
parser.add_argument('-o', '--out_dir', default=None)
args = parser.parse_args()


html_template = \
"""
<!DOCTYPE html>
<html>
    <head>
        <title>Data visualization</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vega/3.0.1/vega.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vega-lite/2.0.0-beta.15/vega-lite.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vega-embed/3.0.0-beta.20/vega-embed.js"></script>
        <style>
            {style}
        </style>
    </head>
    <body>
        {body_html}
        <script type="text/javascript">
            {script_js}
        </script>
    </body>
</html>
"""

style = \
"""
.before-after {
    display: flex;
    flex-direction: row;
}
"""

div_template = \
"""
<div>
    Formula: {formula}
    <br>
    <div class="before-after">
        <div id="vis_before_{i}"></div>
        <div id="vis_after_{i}"></div>
    </div>
</div>
"""


def render_example_group(examples, file_path):
    divs = []
    embeds = []

    # display formula and plots
    # assume that all examples have the same `context` and `targetValue`
    ex = examples[0]
    before = json.dumps(ex['context'])
    after = json.dumps(ex['targetValue'])
    divs.append(div_template.format(i=i, formula=formula))
    embeds.append('vega.embed("#vis_before_{i}", {spec}, opt={opt});'.format(i=i, spec=before, opt='{actions: false}'))
    embeds.append('vega.embed("#vis_after_{i}", {spec}, opt={opt});'.format(i=i, spec=after, opt='{actions: false}'))

    # display utterances
    utterances = sorted([ex['utterance'] for ex in examples])
    for utt in utterances:
        divs.append('{}<br>'.format(utt))

    # create final HTML
    body_html = '\n'.join(divs)
    script_js = '\n'.join(embeds)
    full_html = html_template.format(body_html=body_html, script_js=script_js, style=style)

    with open(file_path, 'w') as f:
        f.write(full_html)


# load data
with open(args.data_path, 'r') as f:
    examples = [json.loads(line) for line in f]
    for i, ex in enumerate(examples):
        assert isinstance(ex, dict), ex

# group by targetFormula
examples_by_formula = defaultdict(list)
for ex in examples:
    examples_by_formula[ex['targetFormula']].append(ex)

# render
if args.out_dir:
    out_dir = args.out_dir
else:
    out_dir = join(os.getcwd(), 'example_viewer')

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

for i, (formula, group) in enumerate(examples_by_formula.items()):
    out_path = join(out_dir, '{}.html'.format(i))
    render_example_group(group, out_path)