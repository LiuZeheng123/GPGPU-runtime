from pathlib import Path
import argparse, concurrent.futures, hashlib, json, os, re, subprocess, sys, traceback
from time import monotonic

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

parser = argparse.ArgumentParser()
for name in ('source','vortex','tools','bindings','out'):
    parser.add_argument('--' + name, type=Path, required=True)
a = parser.parse_args()
repo, vortex, tools, bindings, out = [p.resolve() for p in (a.source,a.vortex,a.tools,a.bindings,a.out)]
out.mkdir(exist_ok=False, parents=True)
evidence = out/'evidence'
evidence.mkdir()
env = os.environ.copy()
for key in ('XCL_EMULATION_MODE','XCLBIN_PATH','VORTEX_CP_POLL_TIMEOUT_S','VORTEX_DRIVER','LD_LIBRARY_PATH'):
    env.pop(key, None)
env.update(VORTEX_SOURCE=str(vortex),VORTEX_PROFILING='0',PYTHONDONTWRITEBYTECODE='1')
def run(label, argv, *, extra=None, cwd=repo):
    log = evidence/(label+'.log')
    command = list(map(str,argv))
    start = monotonic()
    with log.open('xb') as stream:
        p = subprocess.run(command, env={**env, **(extra or {})}, cwd=cwd, stdout=stream,
                           stderr=subprocess.STDOUT, timeout=900)
    rec = dict(label=label,argv=command,exit_code=p.returncode,seconds=round(monotonic()-start,3))
    (evidence/(label+'.command.json')).write_text(json.dumps(rec,indent=2)+'\n')
    print(label,p.returncode,flush=True)
    if p.returncode:
        raise RuntimeError(label+': '+log.read_text(errors='replace')[-800:])
    return log

PY = [sys.executable,'-B']
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
assert head == '63e939bfd2c8b4edeb5c0fc51afb1b4e1eb6923e'
target = repo/'configs/candidates/block32-v1'
lock = target/'target_lock.json'
app = repo/'experiments/iris-u280'
freeze = out/'iris-corpus'
module = out/'modules/iris'
opcorpus = repo/'configs/acceptance/e-runtime-unseen-20261111-v1'
ops = repo/'scripts/e_acceptance'
backends = ('simx','rtlsim','xrtsim')
fixed = json.loads((repo/'configs/target_lock.json').read_bytes())['vortex']['commit']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=vortex,text=True).strip() == fixed
def replay():
    r = json.loads(run('baseline-replay',PY+[repo/'scripts/review_baseline.py']).read_bytes())
    if r['status']!='PASS': raise ValueError('baseline replay did not pass')
    return r
def tests():
    log = run('host-tests',PY+['-m','unittest','discover','-s','tests','-v'])
    s=log.read_text(errors='replace')
    count=int(re.search(r'Ran (\d+) tests?',s).group(1))
    skip=re.search(r'OK \(skipped=(\d+)\)',s)
    skipped=int(skip.group(1)) if skip else 0
    return dict(total=count,skipped=skipped,passed=count-skipped)
def build(name,src,dest):
    tool=repo/'scripts/ptx_module.py'
    run(name+'-prepare',PY+[tool,'prepare',src,'--output',dest,'--hardware',target/'native_smoke.json','--target-lock',lock])
    run(name+'-build',PY+[tool,'build',dest,'--vortex-source',vortex,'--tooldir',tools,'--build-root',out/('build-'+name),'--target-lock',lock])
    run(name+'-validate',PY+[tool,'validate',dest,'--target-lock',lock])
    return digest(dest/'kernel.vxbin')
def execution():
    run('iris-freeze',PY+[app/'freeze.py',freeze])
    iris_image=build('iris',repo/'ptx/samples/iris_nearest_centroid_u32.ptx',module)
    images={}
    for src in sorted((opcorpus/'sources').glob('*.ptx')):
        images[src.stem]=build('op-'+src.stem,src,out/'ops'/src.stem)
    assert len(images)==6
    iris_runs={}
    operator_runs={}
    for b in backends:
        binding=bindings/('binding-'+b+'-v1')/'binding.json'
        meta=json.loads(binding.read_bytes())
        settings={'LD_LIBRARY_PATH':str((binding.parent/meta['library_dir']).resolve()),'VORTEX_DRIVER':meta['driver']}
        scratch=out/('work-'+b)
        scratch.mkdir()
        capture=out/('iris-'+b)
        run('iris-'+b,PY+[app/'capture.py','--inputs',freeze,'--module',module,'--lock',lock,'--binding',binding,'--backend',b,'--output',capture],extra=settings,cwd=scratch)
        review=json.loads(run('iris-review-'+b,PY+[app/'review.py','--frozen',freeze,'--capture',capture,'--binding',binding,'--module',module,'--backend',b]).read_bytes())
        assert review['status']=='PASS' and review['launches']==9
        iris_runs[b]=review
        opout=out/('operators-'+b)
        run('operators-'+b,PY+[ops/'runtime_unseen_run.py','--corpus',opcorpus,'--modules',out/'ops','--binding',binding,'--target-lock',lock,'--backend',b,'--out',opout],extra=settings,cwd=scratch)
        receipt=evidence/('operators-'+b+'.json')
        run('operators-review-'+b,PY+[ops/'runtime_unseen_check.py','--corpus',opcorpus,'--run',opout,'--out',receipt])
        reviewed=json.loads(receipt.read_bytes())
        assert reviewed['status']=='PASS' and reviewed['cases']==48
        operator_runs[b]=reviewed['cases']
    return dict(iris_image_sha256=iris_image,operator_images=images,iris=iris_runs,operators=operator_runs,iris_manifest_sha256=digest(freeze/'manifest.json'))
result=dict(upstream_commit=head,vortex_commit=fixed,tag='baseline-2026-11-23',physical_card='not run on personal account',errors={})
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures={pool.submit(f):name for name,f in [('archive',replay),('host',tests),('new_execution',execution)]}
    for fut in concurrent.futures.as_completed(futures):
        name=futures[fut]
        try: result[name]=fut.result()
        except Exception: result['errors'][name]=traceback.format_exc()
result['status']='FAIL' if result['errors'] else 'PASS'
(evidence/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('FINAL',result['status'],result['errors'],flush=True)
sys.exit(int(bool(result['errors'])))
