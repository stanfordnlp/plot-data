# plot-data

### Extracting examples from querylog
  ```
  jq -c 'if .q[0]=="accept" then .q[1] else empty end' querylog/turk0721.jsonl > examples-turk0721.jsonl
  ```

### Getting data

* Run `python  mturk/create_speaker_hit.py --num-hit 10 --num-assignment 5 --is-sandbox`
    * This creates `hits/timestamp/speaker.HITs.txt`, and `speaker.sample_hit` and deploys the HITs
    * note that assignment_ids are only available once someone works on the hit
    * Wait for these HITs to complete
* In `hits/timestamp/Makefile` set the fig exec id for the server run of this task.
* Restart the server to use the previous speaker data as VegaResources.examplesPath
* Run `python  mturk/create_listener_hit.py hits/SPEAKER_HIT --num-hit 10 --num-assignment 5 --is-sandbox`
    * Wait for these HITs to complete
* In `hits/timestamp` set the fig exec id for the server run, and run `make verify` to get both speaker and listener data
* Alternatively, wait for both speaker and listener hits to complete, and run `make`

### Preprocessing

Make sure you strip the `_id` key from data, since it changes between context and targetValue,
and results in erroneously flagging correct parses as incorrect.  Try running:

    `jq -c 'del(.context.data.values[]?._id) | del(.targetValue.data.values[]?._id)' raw.jsonl > fixed.jsonl`

Alternatively, run `fix_file.sh`, which does the same thing.

### Generating splits

Use `split_data.py` to split data into train/test (no dev since all the Turk data is dev data):

    python split_data.py randomWithNoCanon.jsonl randomWithNoCanon_splitIndep  # Split each example separately
    python split_data.py -s randomWithNoCanon.jsonl randomWithNoCanon_splitSess  # Split by sessionId == MTurk ID
