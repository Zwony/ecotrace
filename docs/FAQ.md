# Frequently Asked Questions

These are the questions that tend to come up once EcoTrace is running
somewhere other than a laptop: in a container, on a CI runner, or in a
production service.

Looking for a specific error message instead? [Support and
Reference](SUPPORT.md) covers the common ones and what EcoTrace does
about them.

---

## Why do my numbers change inside Docker, and what is `/sys/class/powercap`?

On Linux, EcoTrace prefers to read CPU energy from the kernel's powercap
interface. It checks exactly one path, the Intel RAPL package-0 counter:

```
/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
```

That path is the whole of the current detection. AMD processors expose
their own powercap entries under different names, and EcoTrace does not
look for them today, so an AMD host falls through to estimation even
where the kernel is publishing counters.

**EcoTrace never raises or exits when the counter is unavailable — it
switches to estimating instead.** That is deliberate: it keeps EcoTrace
working out of the box on machines with no counters at all. What it logs
on the way, though, depends on which way the check failed, and the three
cases are worth telling apart:

- **The path isn't there at all** (the usual container case). The check
  returns straight away and logs nothing.
- **The path is there but unreadable** (present, wrong permissions). The
  check logs `RAPL found but permission denied.` at `DEBUG`, which you
  won't see at the default `WARNING` level.
- **Either way, once EcoTrace settles on prediction mode on Linux**, it
  logs at `INFO` that the energy sensor is
  `Prediction Mode (Boavizta Advanced Estimation, ~15-20% error margin)`
  and then raises an actual `WARNING`:
  `RAPL access denied! Run with 'sudo' for 0% deviation exact CPU profiling.`
  That warning is visible at the default level, so a container run does
  tell you it fell back — just in a message about `sudo` rather than
  about your container.

For the hardware counters to work inside a container, two things have to
be true:

1. The `/sys/class/powercap` tree is present in the container.
2. `energy_uj` is readable by the user the container runs as. On many
   recent kernels this file is readable only by root.

The quickest way to find out which one is missing is to read the file
yourself, from inside the container:

```bash
cat /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
```

- A number means RAPL is available and EcoTrace will use it.
- `No such file or directory` means condition 1 is failing; the
  powercap tree is not exposed to the container.
- `Permission denied` means condition 2 is failing; the path is there,
  but the container's user cannot read it.

You can ask EcoTrace directly which mode it has selected:

```python
from ecotrace.hardware import HardwareMonitor

print(HardwareMonitor().rapl_available)   # True = hardware counters, False = estimation
```

Two things to keep in mind. EcoTrace reads **package 0 only**
(`intel-rapl:0`), so on a multi-socket machine the other packages aren't
counted. And RAPL is an Intel/AMD feature on Linux — on Windows, on
macOS (Apple silicon included) and on ARM there's nothing to expose, so
you'll get estimation no matter how the container is set up.

---

## What is the difference between RAPL measurement and TDP estimation?

**RAPL** is a measurement. The CPU maintains an energy counter in
hardware and EcoTrace reads it, so the figure reflects what the silicon
actually reported.

**TDP estimation** is a model. When no counter is readable, EcoTrace
maps CPU utilisation onto a fraction of the processor's rated Thermal
Design Power using a piecewise curve from
[Boavizta](https://boavizta.org/):

| CPU load | Share of rated TDP |
|---|---|
| 0% | 12% |
| 10% | 32% |
| 50% | 75% |
| 100% | 102% |

The rated TDP comes from a lookup against EcoTrace's bundled Boavizta
dataset, matched on your CPU model name. **If your CPU is not in that
dataset, EcoTrace assumes 25 W on Apple silicon and 65 W on everything
else** — so an unrecognised server part can be some distance from its
true rating.

Two things about the model are worth knowing before you compare runs.
It's most accurate at full load, where treating power as proportional to
TDP holds up best. And it's deliberately conservative when idle: the
curve builds in a 12% static-leakage floor rather than reporting
near-zero for an always-on service that's doing very little.

For the error figures, see [Accuracy
Validation](benchmarks/07_accuracy_validation.md), but read them
carefully, because that page carries two different numbers. Its most
recent run reports MAPE 40.3% and R² 0.72 against a *synthetic*
reference, which is really a model-against-model comparison. Separately
its discussion cites a typical MAPE of ≤ 15% and R² > 0.90 for runs on a
Linux host with real RAPL access, without data on the page behind that
figure. So: treat 40.3% as the measured result of a model-against-model
comparison, and ≤ 15% as the accuracy the project expects when real
hardware counters are available. Neither number is the one to quote on
its own.

The practical upshot: compare EcoTrace runs with other EcoTrace runs in
the same mode. If you benchmark a RAPL-measured baseline against an
estimated run, you're measuring the change of mode as much as the change
in your code.

---

## How do I run EcoTrace headlessly, in GitHub Actions or a test suite?

Tracking needs no display, and nothing in that path requires a graphical
environment. There's one thing to set, and one assumption that's easy to
get wrong.

**The charting stack is always imported.** `ecotrace/core.py` imports the
reporting module lazily, inside `generate_pdf_report()`, which makes it
look as though `matplotlib` and `fpdf` only load when you ask for a PDF.
They don't: `ecotrace/ml.py` imports that module at module level and the
package's `__init__` imports `ml`, so a bare `import ecotrace` loads
`matplotlib.pyplot` and `fpdf` every time — about 0.46 s of a 0.53 s
import. It isn't a problem, but you can't avoid it by skipping PDF
generation.

**Set the Matplotlib backend explicitly.** Since the import happens
regardless, Matplotlib picks a backend, and which one it picks depends
on the platform rather than on whether a display is actually there. Pin
it so the choice isn't left to chance:

```yaml
# .github/workflows/your-workflow.yml
env:
  MPLBACKEND: Agg
```

or in a shell:

```bash
export MPLBACKEND=Agg
```

That's all you need. EcoTrace doesn't detect CI and there's no flag to
force estimation mode — on a runner without readable counters it falls
back on its own, silently, exactly as above. If you'd like your CI logs
to record which mode a run used, read `HardwareMonitor().rapl_available`
and print it yourself.

---

## How do I silence verbose logs in production?

EcoTrace logs through a standard library logger named `ecotrace`. It is
set to `WARNING` by default, writes to stderr, and prefixes its messages
with `[EcoTrace]`, so it should already be quiet in production. If you
are seeing verbose output, something in your application has lowered the
level — either on this logger or on the root logger it propagates to.

There's no EcoTrace-specific environment variable, setting, or function
for verbosity. It's ordinary `logging` configuration, so whatever you
already do for other libraries works here:

```python
import logging

# Quieten it: only errors and above.
logging.getLogger("ecotrace").setLevel(logging.ERROR)

# Silence it almost entirely.
logging.getLogger("ecotrace").setLevel(logging.CRITICAL)

# Keep it out of your application's root handlers.
logging.getLogger("ecotrace").propagate = False
```

Going the other way: if you're trying to work out why a container fell
back to estimation, turn it up. The RAPL probe records its result at
`DEBUG`, so this is how you see what it found:

```python
import logging

logging.basicConfig()
logging.getLogger("ecotrace").setLevel(logging.DEBUG)
```
