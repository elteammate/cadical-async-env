# CaDiCaL asynchronous environment

This is an implementation of an IPC between a [CaDiCaL SAT solver](https://github.com/arminbiere/cadical) and a python server.

## Example usage

### Step 1: Define the protocol on C++ side

Use interface provided by the [Connection](cadical/src/communicate.hpp) to define the protocol. Here is a simple example which sends an amount of propagations every conflict:

```cpp
// in internal.hpp
int Internal::cdcl_loop_with_inprocessing () {
  // -- snip --
  while (!res) {
    if (unsat)
      res = 20;
    else if (unsat_constraint)
      res = 20;
    else if (!propagate ())
      // First, identify what you want to send with a string
      internal->connection->write_string("propagations");
      
      // Then, send the data itself
      internal->connection->write_u64(stats.blocked); 
      
      // Finally, wait for the server to respond
      internal->connection->wait_for_ok();

      analyze (); // propagate and analyze
    else if (iterating)
      iterate ();                               // report learned unit
      // -- snip --
  }
  // -- snip --
}
```

Of course, you can simply use `connection` here without the `internal->` prefix if you write in the `Internal` class, but it's left here for clarity.

### Step 2: Define the protocol on Python side

First, create a `Router` object. This allows for simple composition of multiple reusable handlers.

```python
from runner import *

router = Router()
```

Then, define a handler for the `propagations` message:

```python
@router.route("stats")
async def stats(conn: Connection, info: RunInfo, data):
    propagations = await conn.read_u64()
    print(f"Propagations: {propagations}")
    await conn.write_ok()
```

It accepts the `Connection` object, the `RunInfo` object containing parameters given to the solver when it's started, and arbitrary data you can pass and modify.

### Step 3: Start the server

Pass all the parameters to the `run_instance` function. It will start the solver and the server, and run the handlers you defined.

```python
await asyncio.gather(*[
    run_instance(
        Path("cadical/build/cadical"),
        [],
        cnf_path,
        router.routes,
        silent=False,
        timeout_seconds=100,
    )
    for cnf_path in cnfs
])
```

Check out [py/experiment.py](py/experiment.py) for a more complete example.

## Parallelism

You can pass a Semaphore to the `run_instance` function to limit the number of solvers running at the same time. This is useful when you have a lot of solvers to run, and you don't want to overload your CPU. You can then temporarily release the semaphore when you are doing (usually GPU-bound or IO-bound) work on Python side.

## Synchronous API

If instead of `runner` you import `srunner` and don't use `async/await`, you will get a synchronous API. This is very useful for debugging and testing since debugging async code can be a pain.

## Should you use this?

This is a low-level API which is not user-friendly. It is intended to be used by modifying the underlying server code and a solver. I highly recommend to instead **implement your own alternative** and use this as a reference, or copy non-trivial parts of the code (such as multiprocess synchronization through asyncio).
