from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time

project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
old=Path('/home/liuzeheng/gpgpu-c-20261110')
previous=Path('/home/liuzeheng/gpgpu-c-20261111')
root=Path('/home/liuzeheng/gpgpu-c-rtl-20261111')
backend=sys.argv[1]
assert backend in ('simx','rtlsim','xrtsim')
suffix=sys.argv[2] if len(sys.argv)>2 else 'v1'
out=root/'evidence'/('c-suite-'+backend+'-'+suffix)
out.mkdir(exist_ok=False)
config=project/'configs/candidates/block32-v1'
native_version='v2' if backend=='xrtsim' else 'v1'
native=(previous/'evidence/c-native-block32-v1/summary.json' if backend=='simx' else root/'evidence'/('c-native-'+backend+'-'+native_version)/'summary.json')
summary=json.loads(native.read_text())
assert summary['status']=='PASS'
lib=Path(summary['build_path'])/'sw/runtime'
env=dict(os.environ,CCACHE_DISABLE='1',VORTEX_SOURCE=str(old/'vortex'),
 VORTEX_DRIVER='xrt' if backend=='xrtsim' else backend,VORTEX_PROFILING='0',LD_LIBRARY_PATH=str(lib))
record=dict(status='RUNNING',backend=backend,commands=[],source_files={},module_files={})
for path in (project/'scripts').glob('*.py'):
 name=str(path.relative_to(project)); data=path.read_bytes()
 record['source_files'][name]=hashlib.sha256(data).hexdigest()
 if path.name in ('ptx_frontend.py','ptx_module.py','ptx_launch.py','ptx_runtime.py','runtime_backends.py',
                  'run_ptx_simx.py','run_ptx_suite.py','bind_simx_runtime.py','verify_ptx_suite_results.py'):
  dest=out/'implementation'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
shutil.copyfile(__file__,out/'driver.py')
def save(): (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
def run(name,command):
 argv=[str(x) for x in command];start=time.perf_counter()
 with (out/(name+'.log')).open('xb') as log:
  result=subprocess.run(argv,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
 record['commands'].append(dict(name=name,argv=argv,exit_code=result.returncode,host_seconds=time.perf_counter()-start,log=name+'.log'))
 save(); print(backend,name,'EXIT',result.returncode,flush=True)
 if result.returncode:raise RuntimeError(name+' failed')
save()
try:
 binding=root/('binding-'+backend+'-'+suffix)
 run('binding',[sys.executable,'-B','scripts/bind_simx_runtime.py','--summary',native,'--target-lock',config/'target_lock.json','--hardware',config/'native_smoke.json','--output',binding])
 for kernel in ('copy','vadd','affine'):
  module=previous/(kernel+'-block32-v1-v1')
  record['module_files'][kernel]={str(p.relative_to(module)):hashlib.sha256(p.read_bytes()).hexdigest() for p in module.iterdir() if p.is_file()}
  run(kernel,[sys.executable,'-B','scripts/run_ptx_suite.py','--backend',backend,'--kernel',kernel,'--module',module,'--binding',binding/'binding.json','--target-lock',config/'target_lock.json','--output',root/'evidence'/('c-'+kernel+'-'+backend+'-'+suffix)])
 record['status']='PASS'
except Exception as exc:record.update(status='FAIL',error=str(exc))
finally:save()
sys.exit(0 if record['status']=='PASS' else 1)
