# 公开验证记录

2026-11-11 C 同步批次：[c-upstream-sync-20261111-v1](c-upstream-sync-20261111-v1/) 保存固定上游快照、导入清单、本人 144 次新执行、九项恢复/故障检查、四路上游历史捕获离线复核及首轮失败。完整原始文件见 personal-validation.zip 与 export.json；上游历史记录和本人新执行分开标识。实板 DEFERRED_BY_USER。

2026-11-11 C 最新：[RTL/AFU 批次](c-runtime-rtl-20261111/)保存 SimX、处理器 RTL、AFU 模型各 840 次 PTX 执行、九次实际恢复、原始分块输入输出、绑定、原生构建日志（含首次失败）、工具来源与服务器只读盘点；[核验记录](c-runtime-rtl-checks-20261111/)保存跨版本读取和七类故意破坏拒绝。此批原样保留哈希与运行路径，不含凭据、SDK 或原生动态库；不是 U280 或 E 独立接收。

本目录按原 run_id 收录选定的命令、退出码、摘要和日志。含本地路径或账号的记录以公开副本单列，示例值不参与原实验的哈希校验。完整日志、参考输入输出、工具包、运行库、XCLBIN、DCP、WSL 磁盘和课程原件在原工作区归档。公开快照用于阅读进度和协作，部分历史复核脚本需要完整本地证据树。

## 原样收录

- [ab-d1-source-20261107-v2/native_smoke.json](ab-d1-source-20261107-v2/native_smoke.json)
- [ab-d1-source-20261107-v2/result.json](ab-d1-source-20261107-v2/result.json)
- [ab-d1-source-20261107-v2/source_manifest.json](ab-d1-source-20261107-v2/source_manifest.json)
- [ab-d1-source-20261107-v2/target_caps.json](ab-d1-source-20261107-v2/target_caps.json)
- [ab-d1-source-20261107-v2/target_lock.json](ab-d1-source-20261107-v2/target_lock.json)
- [ab-d1-source-20261107-v2/target_lock.sha256](ab-d1-source-20261107-v2/target_lock.sha256)
- [ab-d1-source-20261107-v2/resolved_config.cflags](ab-d1-source-20261107-v2/resolved_config.cflags)
- [ab-d2-simx-20261108-v2/summary.json](ab-d2-simx-20261108-v2/summary.json)
- [ab-d3-simx-20261108-v1/summary.json](ab-d3-simx-20261108-v1/summary.json)
- [ab-d3-rtlsim-20261108-v2/summary.json](ab-d3-rtlsim-20261108-v2/summary.json)
- [ab-d3-xrtsim-20261108-v1/summary.json](ab-d3-xrtsim-20261108-v1/summary.json)
- [ab-d4-closeout-20261108-v1/result.json](ab-d4-closeout-20261108-v1/result.json)
- [ab-d5-block32-20261108-v1/summary.json](ab-d5-block32-20261108-v1/summary.json)
- [ab-d5-block32-20261108-v1/logs/01_runner_tests.log](ab-d5-block32-20261108-v1/logs/01_runner_tests.log)
- [ab-d5-closeout-20261108-v1/result.json](ab-d5-closeout-20261108-v1/result.json)
- [ab-d6-closeout-20261108-v1/result.json](ab-d6-closeout-20261108-v1/result.json)
- [ab-d7-closeout-20261109-v1/result.json](ab-d7-closeout-20261109-v1/result.json)
- [ab-d8-closeout-20261109-v1/result.json](ab-d8-closeout-20261109-v1/result.json)
- [ab-d10-link-closeout-20261109-v1/result.json](ab-d10-link-closeout-20261109-v1/result.json)
- [ptx-frontend-host-20261108-v3/summary.json](ptx-frontend-host-20261108-v3/summary.json)
- [ptx-frontend-host-20261108-v3/logs/01_python_tests.log](ptx-frontend-host-20261108-v3/logs/01_python_tests.log)
- [ptx-frontend-host-20261108-v3/logs/02_host_compiler.log](ptx-frontend-host-20261108-v3/logs/02_host_compiler.log)
- [ptx-frontend-host-20261108-v3/logs/03_copy_u32_frontend.log](ptx-frontend-host-20261108-v3/logs/03_copy_u32_frontend.log)
- [ptx-frontend-host-20261108-v3/logs/04_copy_u32_host_compile.log](ptx-frontend-host-20261108-v3/logs/04_copy_u32_host_compile.log)
- [ptx-frontend-host-20261108-v3/logs/05_copy_u32_host_run.log](ptx-frontend-host-20261108-v3/logs/05_copy_u32_host_run.log)
- [ptx-frontend-host-20261108-v3/logs/06_vadd_u32_frontend.log](ptx-frontend-host-20261108-v3/logs/06_vadd_u32_frontend.log)
- [ptx-frontend-host-20261108-v3/logs/07_vadd_u32_host_compile.log](ptx-frontend-host-20261108-v3/logs/07_vadd_u32_host_compile.log)
- [ptx-frontend-host-20261108-v3/logs/08_vadd_u32_host_run.log](ptx-frontend-host-20261108-v3/logs/08_vadd_u32_host_run.log)
- [ptx-frontend-host-20261108-v3/logs/09_affine_u32_frontend.log](ptx-frontend-host-20261108-v3/logs/09_affine_u32_frontend.log)
- [ptx-frontend-host-20261108-v3/logs/10_affine_u32_host_compile.log](ptx-frontend-host-20261108-v3/logs/10_affine_u32_host_compile.log)
- [ptx-frontend-host-20261108-v3/logs/11_affine_u32_host_run.log](ptx-frontend-host-20261108-v3/logs/11_affine_u32_host_run.log)
- [ptx-frontend-host-20261108-v3/logs/12_semantics_probe_frontend.log](ptx-frontend-host-20261108-v3/logs/12_semantics_probe_frontend.log)
- [ptx-frontend-host-20261108-v3/logs/13_semantics_probe_host_compile.log](ptx-frontend-host-20261108-v3/logs/13_semantics_probe_host_compile.log)
- [ptx-frontend-host-20261108-v3/logs/14_semantics_probe_host_run.log](ptx-frontend-host-20261108-v3/logs/14_semantics_probe_host_run.log)
- [ptx-frontend-host-20261108-v3/logs/15_fault_eager_load_compile.log](ptx-frontend-host-20261108-v3/logs/15_fault_eager_load_compile.log)
- [ptx-frontend-host-20261108-v3/logs/16_fault_eager_load_run.log](ptx-frontend-host-20261108-v3/logs/16_fault_eager_load_run.log)
- [u280-link-20261109-155638-456/returned/build/clock_check.stdout](u280-link-20261109-155638-456/returned/build/clock_check.stdout)
- [u280-runtime-20261109-v4/returned/runtime/ldd_libvortex-xrt.stdout](u280-runtime-20261109-v4/returned/runtime/ldd_libvortex-xrt.stdout)
- [u280-runtime-20261109-v4/returned/runtime/ldd_libvortex.stdout](u280-runtime-20261109-v4/returned/runtime/ldd_libvortex.stdout)
- [u280-runtime-20261109-v4/returned/runtime/compiler.stdout](u280-runtime-20261109-v4/returned/runtime/compiler.stdout)
- [u280-runtime-20261109-v4/returned/runtime/glibc.stdout](u280-runtime-20261109-v4/returned/runtime/glibc.stdout)
- [u280-timing-review-20261109-v2/result.json](u280-timing-review-20261109-v2/result.json)
- [u280-board-input-20261109-v1/result.json](u280-board-input-20261109-v1/result.json)
- [ab-d13-input-checks-20261109-v1/result.json](ab-d13-input-checks-20261109-v1/result.json)
- [ab-d13-script-checks-20261109-v2/result.json](ab-d13-script-checks-20261109-v2/result.json)
- [ab-d13-script-checks-20261109-v2/tests.log](ab-d13-script-checks-20261109-v2/tests.log)
- [ab-d13-source-checks-20261109-v1/result.json](ab-d13-source-checks-20261109-v1/result.json)

## 脱敏副本

- [ab-d1-source-20261107-v2/commands.json](ab-d1-source-20261107-v2/commands.json)
- [ab-d9-closeout-20261109-v1/result.json](ab-d9-closeout-20261109-v1/result.json)
- [ptx-frontend-closeout-20261108-v1/result.json](ptx-frontend-closeout-20261108-v1/result.json)
- [u280-preflight-20261109-100406-629/returned/build/result.json](u280-preflight-20261109-100406-629/returned/build/result.json)
- [u280-link-20261109-155638-456/returned/build/result.json](u280-link-20261109-155638-456/returned/build/result.json)
- [u280-archive-20261109-v5/returned/build/result.json](u280-archive-20261109-v5/returned/build/result.json)
- [u280-runtime-20261109-v4/returned/runtime/result.json](u280-runtime-20261109-v4/returned/runtime/result.json)
- [u280-readiness-review-20261109-v2/result.json](u280-readiness-review-20261109-v2/result.json)
