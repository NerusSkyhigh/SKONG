# SKONG

SKONG (System for Keeping Organized Numerical Goals) is a lightweight Python CLI
to track computational project states and submit batch jobs.

## Scheduler-aware submission

`skong sub` and `skong continue` can now submit to either PBS or Slurm.

By default, SKONG auto-detects the scheduler and submits with:

- PBS: `qsub -v RESTART=<0|1> <script>`
- Slurm: `sbatch --export=ALL,RESTART=<0|1> <script>`

### Auto-detection order

When `--scheduler auto` is used (default), scheduler selection follows:

1. Explicit CLI value (`--scheduler pbs|slurm`)
2. Environment override (`SKONG_SCHEDULER=pbs|slurm`)
3. Allocation environment hints (`SLURM_*` or `PBS_*` variables)
4. Binary availability in `PATH` (`sbatch` / `qsub`)

If both `sbatch` and `qsub` are available and no prior hint exists, SKONG picks
Slurm.

## Job script defaults

If `--job` is omitted, the default script name depends on scheduler:

- PBS: `job.pbs`
- Slurm: `job.slurm`

You can always override this with `--job <filename>`.

## Examples

Auto-detect scheduler and submit up to 20 initialized jobs:

```bash
skong sub 20 --path .
```

Force PBS:

```bash
skong sub 10 --scheduler pbs --job job.pbs --path .
```

Force Slurm:

```bash
skong sub 10 --scheduler slurm --job job.slurm --path .
```

Re-submit partial jobs and let SKONG auto-detect:

```bash
skong continue 5 --path .
```

Use environment override (helpful in scripts):

```bash
export SKONG_SCHEDULER=slurm
skong sub 10 --path .
```
