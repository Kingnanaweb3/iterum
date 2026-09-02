# Iterum

An agent that pays other agents for work, and remembers how each one behaved.

Think of a builder who hires the same three plumbers over and over.
The cheap one turns up late, does a bad job, and once took the money and left.
After a while the builder stops calling him, and pays more for someone who shows up.

Iterum is that builder, except it is software, and the memory is the whole product.

## What it actually does

The agent needs to check if a token contract is safe before touching it.
Three sellers offer that check. They cost different amounts and they are not equally honest.

* Aegis, 0.05 USDC, careful and slow to break
* Meridian, 0.02 USDC, fine most days, sometimes just does not answer
* Nadir, 0.005 USDC, cheapest, sometimes takes your money and tells you a lie

If you only look at the price, you always pick Nadir.
If you remember what happened last time, you stop doing that.

## Why memory is the whole thing

After every purchase the agent writes down what happened.
Did the seller answer. Was the answer fresh. Was the answer true.

Next time, before it spends a cent, it reads that record.
The record decides who it buys from, how much it will risk, and whether it pays up front or holds the money back.

None of that is in a settings file. There is no line anywhere that says "do not trust Nadir".
The agent works it out from what it wrote down.

## What breaks if you delete the memory

Everything.

Without the record every seller looks the same, so the agent picks the cheapest one every single time.
It gets robbed by Nadir on Monday and goes straight back to Nadir on Tuesday.

The product is not slower or worse without memory. It cannot exist.
That is the test, and Iterum passes it.

## The four levels

Every seller sits on one of four rungs, based only on its record.

| Level | What it means | How the agent pays |
| --- | --- | --- |
| trusted | Long clean record | Pays on delivery, bigger budget |
| provisional | New, or mostly fine | Pays on delivery, normal budget |
| guarded | Has messed up | Holds the money back, small budget |
| blocked | Messed up badly or often | Will not buy from it at all |

## Not all mistakes are equal

A seller that goes quiet costs you a fee.
A seller that gives you a wrong answer costs you the thing you were protecting.

So a lie hurts its score more than silence does.
This is the same reason you forgive a friend who forgets to call, but not one who lies to your face.

| What happened | Effect on score |
| --- | --- |
| Gave a good answer | up 8 |
| Answered but slowly | up 2 |
| Answer was old | down 10 |
| Took the money, gave nothing | down 22 |
| Gave a wrong answer | down 30 |
| Our own payment failed | no change, not their fault |

## Old news fades

A mistake from three weeks ago should not follow a seller around forever.
Every record loses half its weight each week.

So a seller can come back, but slowly, the way a bad review stops mattering after a year of good ones.

## Saying sorry is not enough

One good job after a bad one does not get a seller off the naughty step.
It has to do two good jobs in a row.

Otherwise a lucky day would wipe out a real problem, and that is how you get robbed twice.

## Sometimes it takes a chance

If the agent only ever used its favourite seller, it would never find out that anyone else improved.
So now and then it tries someone it has not used before.

Same reason you occasionally order from the new place instead of the usual one.

## Where the memory lives in the code

| What | File | Function |
| --- | --- | --- |
| The only place Sibyl Memory is touched | `src/iterum/memory.py` | `write_counterparty`, `read_counterparty`, `append_outcome_event` |
| Writing down what happened | `src/iterum/graph.py` | `record_transaction` |
| Reading the record before deciding | `src/iterum/graph.py` | `get_history` |
| Rebuilding the record from scratch | `src/iterum/graph.py` | `rebuild_from_journal` |
| Turning the record into a decision | `src/iterum/terms.py` | `derive_terms` |
| Proof a fresh session remembers | `tests/test_cold_recall.py` | whole file |

## Two places it keeps things

The journal is the diary. Every purchase gets one line and nothing is ever edited.
The entity is the summary page. It gets rewritten every time.

If the summary is ever wrong, `rebuild_from_journal` builds it again from the diary.
The diary is the truth. The summary is just faster to read.

## What is real and what is not

Real: the money. Every purchase is a live x402 payment in USDC on Base Sepolia.
Real: the failures. Sellers fail on a dice roll, not on a script.
Real: the memory. Sibyl Memory, on disk, read by a brand new process that saw none of it happen.

Not real: the safety checks themselves. Iterum is not a real contract scanner and never claims to be.
The verdicts are made up. What is being tested is the memory, not the security tool.

## The settings used in the recorded demo

These live in `.env` so you can turn the failures up while testing.
The recorded demo used these values.

    NADIR_WRONG_RATE=0.30
    NADIR_DEAD_RATE=0.06
    NADIR_STALE_RATE=0.10
    MERIDIAN_TIMEOUT_RATE=0.20
    AEGIS_FAIL_RATE=0.05
    ITERUM_EXPLORE_RATE=0.30

## Partner stacks

Base. Every purchase is an x402 payment that really happens.
The payment is the thing memory is deciding about, so it is not bolted on.

## Running it

    pip install -e .
    cp .env.example .env
    ./run-providers.sh          # in one terminal
    ./reset-memory.sh
    python demo/run_demo.py 18  # in another
    python demo/run_demo.py 1 status

## Prior work

Iterum was prototyped before the build window opened. Everything below was written before September 1 and is listed with dates.

* Project scaffold and layout, Aug 17
* Sibyl Memory adapter, Aug 17
* Cold recall test passing against real Sibyl storage, Aug 17
* `graph.py`, Aug 19
* `terms.py`, Aug 19
* Tests for the scoring rules, Aug 19
* Domain switched to contract checks, Aug 21
* No agent, no sellers, and no payments were built before September 1

## Licence

MIT.
