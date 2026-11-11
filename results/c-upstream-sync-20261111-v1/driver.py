from pathlib import Path
import hashlib,json,os,subprocess,sys,time
work=Path(__file__).resolve().parent
repo=work/'GPGPU_U280_winter2026'
reference=work/'Vortex-U280-reference-2aad3a0'
root=Path('/home/liuzeheng/gpgpu-c-sync-20261111-v2')
root.mkdir(exist_ok=False)
out=root/'evidence';out.mkdir()
(out/'driver.py').write_bytes(Path(__file__).read_bytes())
old=Path('/home/liuzeheng/gpgpu-c-20261110')
env=dict(os.environ,VORTEX_SOURCE=str(old/'vortex'),VORTEX_PROFILING='0',
 PATH=str(old/'host-tools/cmake-3.31.10-linux-x86_64/bin')+':'+os.environ['PATH'])
record=dict(status='RUNNING',commands=[],source_files={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('scripts','tests') for p in (repo/folder).rglob('*.py')},
 board='DEFERRED_BY_USER',scope='personal reproduction of upstream code and frozen E corpus, not a newly independent E acceptance')
def save(): (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
def run(label,command,timeout=300):
 argv=[str(x) for x in command];start=time.monotonic()
 with (out/(label+'.log')).open('xb') as log:
  p=subprocess.run(argv,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
 record['commands'].append(dict(label=label,argv=argv,exit_code=p.returncode,seconds=time.monotonic()-start,log=label+'.log'))
 save();print(label,'EXIT',p.returncode,flush=True)
 if p.returncode:raise RuntimeError(label+' failed')
save()
try:
 run('unittests',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v'])
 corpus=repo/'configs/acceptance/e-runtime-unseen-20261111-v1'
 for backend,folder in [('simx','e-runtime-unseen-sim-20261111-v1/simx'),('rtlsim','e-runtime-unseen-sim-20261111-v1/rtlsim'),('xrtsim','e-runtime-unseen-sim-20261111-v1/xrtsim'),('u280','e-u280-unseen-20261111-v1/returned/execution/e-unseen')]:
  run('upstream-archive-'+backend,[sys.executable,'-B','scripts/e_acceptance/runtime_unseen_check.py','--corpus',corpus,'--run',reference/'results'/folder,'--out',out/('upstream-'+backend+'-recheck.json')])
 config=repo/'configs/candidates/block32-v1'
 for source in sorted((corpus/'sources').glob('*.ptx')):
  name=source.stem;module=root/'modules'/name
  run(name+'-prepare',[sys.executable,'-B','scripts/ptx_module.py','prepare',source,'--output',module,'--target-lock',config/'target_lock.json','--hardware',config/'native_smoke.json'])
  run(name+'-build',[sys.executable,'-B','scripts/ptx_module.py','build',module,'--target-lock',config/'target_lock.json','--vortex-source',old/'vortex','--build-root',root/('build-'+name),'--tooldir',old/'tools'])
 for backend in ('simx','rtlsim','xrtsim'):
  binding=Path('/home/liuzeheng/gpgpu-c-rtl-20261111')/('binding-'+backend+'-v1')/'binding.json'
  identity=json.loads(binding.read_text())
  env.update(VORTEX_DRIVER=identity['driver'],LD_LIBRARY_PATH=identity['library_dir'])
  run(backend+'-capture',[sys.executable,'-B','scripts/e_acceptance/runtime_unseen_run.py','--corpus',corpus,'--modules',root/'modules','--binding',binding,'--target-lock',config/'target_lock.json','--backend',backend,'--out',out/backend],1800)
  run(backend+'-check',[sys.executable,'-B','scripts/e_acceptance/runtime_unseen_check.py','--corpus',corpus,'--run',out/backend,'--out',out/(backend+'-acceptance.json')])
  for mode in ('timeout','cp-fault','canary'):
   run(backend+'-'+mode,[sys.executable,'-B','scripts/validate_runtime_recovery.py','--worker','--backend',backend,'--mode',mode,'--module',root/'modules/copy','--binding',binding,'--lock',config/'target_lock.json','--output',out/(backend+'-'+mode)],300)
 record.update(status='PASS',exit_code=0)
except Exception as exc:record.update(status='FAIL',exit_code=1,error=str(exc))
finally:save()
sys.exit(record['exit_code'])
