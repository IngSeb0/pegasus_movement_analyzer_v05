from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent/'runtime'))
import run_study as runner
for condition in runner.read(runner.ROOT/'SPECS.json'):
    runner.prepare(dict(id=condition,condition=condition,block=1))
    print(condition,flush=True)
