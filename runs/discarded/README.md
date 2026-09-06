# Discarded — pre-correction C-arm calls, must never be pooled

All files here were produced against `atlas_c_v1.csv` BEFORE commit 5c63bb0
(the c2 point-3 correction). They used the old c2 wording, whose universal
"will not behave correctly on inputs other than the one shown" claim is false
on 12 of 15 c2 rows.

Cause: a `pkill -f "run_name c_t1"` pattern that did not match the real command
line (`--run-name c_t1`), so the first c_t1 process was reported killed but kept
running for ~16 minutes and wrote 43 rows from the in-memory pre-correction CSV.
It was killed by PID once detected.

These rows are not a valid partial of any run and are not resumable: a
`--resume` against them would skip tuples whose transcripts differ from the
corrected dataset.
