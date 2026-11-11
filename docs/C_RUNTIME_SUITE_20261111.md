# C 第三批：三类 PTX 与 32 线程 SimX 验证

2026-11-11，LiuZeheng123。真实执行链路为 PTX → 前端 v1.2 → Vortex SIMT 编译 → vxbin → Vortex2 Runtime → SimX → 读回比较。代码和证据保存到个人 [GPGPU-runtime](https://github.com/LiuZeheng123/GPGPU-runtime)，不代表团队共享仓库已合并。

## 本轮结果

| PTX 样例 | 16 线程基线 | 32 线程候选 | 候选中 block=32 |
|---|---:|---:|---:|
| copy_u32（复制） | 96/96 PASS | 168/168 PASS | 24 |
| vadd_u32（相加） | 96/96 PASS | 168/168 PASS | 24 |
| affine_u32（alpha*x+y，模 2^32） | 288/288 PASS | 504/504 PASS | 72 |
| 总计 | **480/480** | **840/840** | **120** |

六个独立执行进程均退出 0。每组还实际触发一次 native status=7 的超时，随后排空队列、generation 0→1、拒绝旧 buffer/event/module、重新装载和计算，6/6 PASS。每组记录 19 个拒绝检查，含超额 block、越界传输、非对齐指针、参数数量、外来句柄、第二模块、在途操作、超时状态和过期句柄。完整 Linux 回归 152 项：**138 通过、14 跳过、0 失败**，退出 0；其中真实固定头文件的 ctypes ABI 检查通过。跳过是历史材料/默认源码位置缺项，未计为通过。

输入覆盖长度 0/1/7/15/16/17/31/32/33/65/257/1024，两套确定性输入、16/32 字节指针偏移、完整输入不变和输出前后哨兵。affine 的 alpha=0/1/0xffffffff，包含无符号乘法/加法溢出。这里验证输出与保护区，未采集本轮 PTX 的 LSU 访问 trace，不能将 N=0 输出正确解释为所有访存行为均已观测。

## 配置和环境

- 固定 Vortex `7fe19369587c087f902c3e2bc2add612aa910a95`，工具链 `8c64cf921d3c6c456e80f00d24482d0aa2153a82`，没有修改上游源码。
- 基线：`configs/`，RV64 / 1 core / 4 warps / 4 threads；复用 11 月 10 日通过原生 smoke 的运行库，三类 PTX 均重新构建。
- 候选：`configs/candidates/block32-v1/`，RV64 / 1 core / 8 warps / 4 threads；单独构建真实原生 SimX 并通过 demo，使用另一套 binding 和三个新设备模块。
- 根 lock/caps 不改变，候选不替换基线，也不是 32-lane warp 兼容声明。
- 环境为现有 Ubuntu 24.04 WSL，glibc 2.39、G++ 13.3、Python 3.12、独立 CMake 3.31.10。Linux 工作区 `/home/liuzeheng/gpgpu-c-20261111`；固定源码和 SDK 复用 `/home/liuzeheng/gpgpu-c-20261110`。

本轮没有登录配置板卡、替换服务器系统库或烧录 FPGA。当前结果不属于 PTX RTL、XRT AFU、U280 或 E 的独立验收。

## 变更与问题修复

1. 新增 `run_ptx_suite.py`，同一测试入口接收三类 kernel，通过真实 Runtime 执行，保存完整输入、预期和观察字节、拒绝结果、超时恢复及主机耗时。oracle 用于比较，不替代设备执行。
2. 前端升为 `ptx-vx-frontend-v1.2`。首次 copy 真实编译因原地 `cvta.to.global.u64 %a0, %a0` 生成 C++ 自赋值，被固定 Clang 的 `-Wself-assign/-Werror` 拒绝。修正为显式空操作，保留谓词和源码映射；类型、指针来源与已定义性检查仍先执行。原地 mov 同样处理，未降低警告等级，也未改变 ABI、PTX 白名单或算术语义。
3. Runtime 在第二模块装载前返回 E_BUSY，防止固定地址镜像重叠。卸载或成功恢复后仍可重新装载。`query_caps` 暴露 `max_modules=1` 和首个原生错误的副本，后续失败不覆盖原故障，调用方无法修改内部诊断。
4. 新增 `verify_ptx_suite_results.py`，独立于执行器代码读取原始捕获，校验哈希、覆盖矩阵、算术、整个输入输出和恢复记录。它由同一实施者编写，只是归档一致性复查，不是 E 独立验收。

首次失败目录 `c-suite-smoke-v1` 和 `modules/copy-smoke-v1` 完整保留；最终成功基线用 v2，候选用独立 block32-v1-v1。Windows 前端测试曾因沙箱临时目录 PermissionError 未完成，之后在实际 Linux 环境的完整回归通过；不将该环境错误归作设备失败。

## 耗时记录的含义

每例保存 `host_timing_ns`，分别记录同步 H2D、launch、wait、D2H 和 compare；汇总含样本数、最小值、中位数、最大值。构建驱动另保存命令耗时和退出码，setup 保存打开 context 和模块装载时间。

这些是 Python `perf_counter_ns` 的主机墙钟时间，包含仿真、运行库与宿主开销；未排除首例、没有控制宿主竞争负载，各配置的用例分布也不同。**不把这些数值解释为 GPU kernel 时间、FPGA 吞吐或两套配置的性能比较。**

## 证据与复查

证据根目录：[results/c-runtime-suite-20261111](../results/c-runtime-suite-20261111/)。

- `c-{copy,vadd,affine}-smoke-v2/` 和 `c-{copy,vadd,affine}-block32-v1-v1/`：原始 result.json、统计日志和分块 `cases-*.tgz`，归档内路径为 `cases/<id>/*.bin`。
- `c-suite-smoke-v2/`、`c-suite-block32-v1-v1/`：实际完整命令、退出码、耗时、stdout 和运行时源码快照。
- `modules/`：六个通过模块及首次失败模块，含 image、manifest、源代码、编译日志和反汇编。
- `bindings/`、`c-native-block32-v1/`：运行库绑定及候选真实原生构建记录；完整动态库保留在 Linux 原工作区。
- `c-final-checks-v1/`：完整 Linux 回归与源文件哈希。
- `verification.json`、`export.json`：1320 组归档读回后重新核算通过，以及导出文件 SHA-256。大型 SDK/运行库不上传 GitHub。

任何平台只需 Python 3 即可复查归档，命令不执行设备：

```bash
python3 -B scripts/verify_ptx_suite_results.py results/c-runtime-suite-20261111/c-copy-smoke-v2
python3 -B scripts/verify_ptx_suite_results.py results/c-runtime-suite-20261111/c-affine-block32-v1-v1
```

## 原环境复跑示例

从项目根目录执行，结果路径必须取新名字。每个进程只加载一套动态库；这里使用已经成功构建的 32 线程候选：

```bash
export RUN_ROOT=/home/liuzeheng/gpgpu-c-20261111
export VORTEX_DRIVER=simx
export VORTEX_PROFILING=0
export LD_LIBRARY_PATH="$RUN_ROOT/build-native-block32-v1/sw/runtime"
python3 -B scripts/run_ptx_suite.py --kernel affine \
  --module "$RUN_ROOT/affine-block32-v1-v1" \
  --binding "$RUN_ROOT/binding-block32-v1-v1/binding.json" \
  --target-lock configs/candidates/block32-v1/target_lock.json \
  --output "$RUN_ROOT/evidence/c-affine-block32-new-run"
```

在新机器上，先按固定版本准备工具链、源码与 Ramulator 依赖。原生构建入口为 `run_native_smoke.py --target-profile block32-v1`，使用新 `--build-dir` / `--run-id` 和 `--jobs 2`；通过后以相同候选 lock/config 执行 `ptx_module.py prepare/build`、`bind_simx_runtime.py`。基线改用 `--target-profile smoke` 与根 `configs/`，不可混用库或镜像。全部实际命令见上述 `c-suite-*/result.json` 和原生 summary。

## 剩余工作

待 E 使用独立 oracle 与用例接收；待 A/B 对接 PTX 的 RTL/AFU 和 U280 数据通路、完成语义与真实故障恢复。Runtime 仍只启用 SimX、单队列、单模块、单任务在途；当前恢复仅为有界排空，不承诺安全 abort、硬复位或 PCIe/DMA 隔离。团队共享仓库接收和合并尚未完成。
