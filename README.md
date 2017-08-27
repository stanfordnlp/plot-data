# plot-data

### Extracting examples from querylog
  ```
  jq 'if .q[0]=="accept" then .q[1] else empty end' querylog/turk0721.jsonl > examples-turk0721.jsonl
  ```

### Preprocessing

Make sure you strip the `_id` key from data, since it changes between context and targetValue,
and results in erroneously flagging correct parses as incorrect.  Try running:

    jq -c 'del(.context.data.values[]?._id) | del(.targetValue.data.values[]?._id)' raw.jsonl > fixed.jsonl

Alterantively, run `fix_file.sh`, which does the same thing.

### Examples

* megha.ex.jsonl: 31 unique utterances, 121 distinct examples
* sidaw.ex.jsonl: 14 unique utterances
* turk0721.ex.jsonl: 226 unique utterances, 561 examples 
* turk0803_interactive.jsonl: 241 unique utterances, 241 examples - generated from Mechanical Turk Experiment with full interactivity
