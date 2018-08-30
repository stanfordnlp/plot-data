"""
visualize the aggregated speaker table
"""
import argparse
import json
import os
from collections import defaultdict
from os.path import join

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input')
parser.add_argument('-o', '--output', default=None)
parser.add_argument('--with-utterances', default=False, action='store_true')
OPTS = parser.parse_args()


html_template = \
"""
<!DOCTYPE html>
<html>
    <head>
        <style>
            {style}
        </style>
    </head>
    <body>
        <table>
          <tbody>
            {rows}
          </tbody>
        </table>
    </body>
</html>
"""

row_template = \
"""
<tr class="odd">
<td>{WorkerId}</td>
<td>{accuracy:.1f}</td>
<td>{correct}</td>
<td>{wrong}</td>
<td>{skip}</td>
<td><div class="normal">{utterances}</div></td>
</tr>
"""

script_js = ''
style = \
"""
table {
  margin: 5px;
  margin-left: 10px;
}

td {
  max-width: 350px;
  padding: 5px;
  overflow: scroll;
  vertical-align: top;
}

.normal {
  height: 1em;
  width: 500px;
  overflow: hidden;
  text-overflow:ellipsis;
}

.full {
  height: auto;
  width: auto;
}

tr.even {
  background: #eee;
  border-bottom: 1px dotted #ddd;
}

tr.odd {
  background: #fff;
  border-bottom: 1px dotted #eee;
}
"""

def get_html(json_data):
    rows = []
    for k, v in json_data.items():
        default_keys = ['correct', 'wrong', 'skip']
        for s in default_keys:
            if s not in v['stats']:
                v['stats'][s] = 0
        if OPTS.with_utterances:
            utterances = '<br/>'.join(v['utterances'])
        else:
            utterances = ''

        acc = v['stats']['correct'] / sum(v['stats'][s] for s in default_keys)
        row = row_template.format(WorkerId=k, accuracy=100*acc, utterances=utterances, **v['stats'])
        rows.append(row)

    full_html = html_template.format(rows='\n'.join(rows), script_js=script_js, style=style)
    return full_html

data = json.load(open(OPTS.input, 'r'))

with open(OPTS.output, 'w') as f:
    f.write(get_html(data))
