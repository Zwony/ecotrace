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
  Both messages come from `EcoTrace.__init__` and are only emitted when
  the instance is created without `quiet=True`; with `quiet=True` the
  fallback happens silently. They also go through the `ecotrace` logger,
  so if you've raised its level above `WARNING` (see
  [silencing logs](#how-do-i-silence-verbose-logs-in-production)) you
  won't see the warning either. With the defaults, though, the warning is
  visible, so a container run does tell you it fell back — just in a
  message about `sudo` rather than about your container.

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

You can ask EcoTrace directly which mode it has selected. There are
three, not two, so checking `rapl_available` on its own isn't enough —
`False` there still leaves powermetrics in play on a Mac:

```python
from ecotrace.hardware import HardwareMonitor

hw = HardwareMonitor()
if hw.rapl_available:
    print("RAPL (exact hardware)")
elif hw.apple_silicon_available:
    print("Apple Silicon powermetrics (exact hardware)")
else:
    print("Prediction Mode (Boavizta estimation)")
```

That order mirrors the one EcoTrace uses internally when it picks a
sensor.

Two things to keep in mind. EcoTrace reads **package 0 only**
(`intel-rapl:0`), so on a multi-socket machine the other packages aren't
counted. And powercap RAPL is a Linux feature: on Windows and on Linux
hosts without a readable `intel-rapl` counter you get estimation. macOS
is the exception worth knowing — on Apple silicon EcoTrace probes
`sudo -n powermetrics`, and when that succeeds it measures the CPU
package directly rather than estimating. Without passwordless `sudo` the
probe fails and you fall back to estimation, which is why the same Mac
can report differently depending on how the process was launched.

---

## What is the difference between RAPL measurement and TDP estimation?

The short answer is where the *power* number comes from. Neither mode
reports a raw sensor reading: both feed into the same calculation in
`core._compute_carbon()`, which scales the result, adds RAM energy on
top, and converts to grams of CO2 using the configured carbon intensity.

**RAPL** is a hardware measurement. The CPU maintains an energy counter
and EcoTrace reads the delta across your measured window. That delta is
not reported as-is: it is multiplied by normalised CPU utilisation
before it becomes watt-hours, so what you see is derived from the
counter rather than equal to it. If your process is one of several on a
busy box, that scaling is what attributes a share of package energy to
your code rather than charging you for the whole socket.

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
regardless, Matplotlib picks a backend. Its automatic choice depends on
which GUI toolkits and display environment it finds, and that can vary
between runners and images in ways that are easy to overlook. Pinning
the non-interactive `Agg` backend in headless CI keeps the choice
predictable:

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
back on its own, logging the `RAPL access denied!` warning described
above unless the instance was created with `quiet=True` or the
`ecotrace` logger's level hides it. If you'd like your CI logs
to record which mode a run used, print it yourself with the three-way
check above — on a Linux runner `rapl_available` is the one that
matters, but the same snippet works everywhere.

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
