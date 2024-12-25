from runner import *
from pathlib import Path

cnfs = map(Path, [
    "pigeonhole.cnf",
])

router = Router()

@router.route("stats")
async def stats(conn: Connection, info: RunInfo, data):
    result = {}
    while (name := await conn.read_str()) != "end":
        if name == "time":
            result[name] = await conn.read_f64()
        else:
            result[name] = await conn.read_u64()
    print(result)
    await conn.write_ok()


@dataclasses.dataclass
class ReductionProblem:
    num_vars: int
    levels: list[int]
    vals: list[int]
    clauses: list[list[Clause]]
    reducible_ids: list[int]


@router.route("reduce")
async def reduce(conn: Connection, info: RunInfo, data):
    num_vars = await conn.read_u64()
    levels = [-1] * num_vars
    vals = [-1] * num_vars
    for i in range(num_vars):
        vals[i] = await conn.read_i8()
        levels[i] = await conn.read_i32()
    num_clauses = await conn.read_u64()
    clauses = [await conn.read_clause() for _ in range(num_clauses)]
    num_reducible = await conn.read_u64()
    num_target = await conn.read_u64()
    reducible_ids = [await conn.read_u64() for _ in range(num_reducible)]
    conflicts = await conn.read_u64()

    problem = ReductionProblem(
        num_vars=num_vars,
        levels=levels,
        vals=vals,
        clauses=clauses,
        reducible_ids=reducible_ids,
    )

    # print(num_vars, levels, vals, clauses, num_reducible, num_target, reducible_ids)
    print(num_vars)
    await conn.write_ok()
    await conn.write_u32(1)
    await conn.write_u64(reducible_ids[0])


async def main():
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


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
