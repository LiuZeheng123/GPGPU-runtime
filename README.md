# GPGPU Runtime：Vortex / PTX / U280

刘泽衡（[LiuZeheng123](https://github.com/LiuZeheng123)）的数字 GPGPU 项目工作仓库，保存 **C 分工：Runtime 与上板对接** 的代码、测试和实验记录。

目标是让受支持的 PTX 程序经过编译，在 Vortex GPGPU 上执行，并由主机程序写入输入、发起计算、等待完成和读回结果。当前已跑通 **PTX vadd → Vortex2 Runtime → SimX**；U280 实板对接仍待完成。

> 截至 2026-11-10：本阶段的软件联调完成，不代表整个项目、完整 PTX/CUDA 兼容或 U280 板上验证完成。

## 来源与协作关系

- 项目基于同学的 [Vortex-U280](https://github.com/slishysun974/Vortex-U280)，继承基线为 `46dd01406a98ee6eab451a435c8a761b4b6a9eea`。保留原有 A/B 平台、前端、文档及选定实验记录；这些历史成果不能全部归为本人的工作。
- 团队共享空间：[sunshawn-new/GPGPU_U280_winter2026](https://github.com/sunshawn-new/GPGPU_U280_winter2026)。本仓库保存个人进度，后续按团队约定同步 C 的改动；个人上传不等于团队已合并。
- 处理器上游：[vortexgpgpu/vortex](https://github.com/vortexgpgpu/vortex)，固定提交 `7fe19369587c087f902c3e2bc2add612aa910a95`；工具链 v3.0.1，固定提交 `8c64cf921d3c6c456e80f00d24482d0aa2153a82`。
- 当前方向为 Vortex 与 PTX P0 子集，不包含模拟电路。原项目、第三方源码及其许可证/署名保持各自归属，本仓库不额外授予第三方代码许可。

## 已完成的阶段成果

```text
PTX 源码 → 前端检查与代码生成 → 设备包装与编译 → kernel.vxbin
                                                       ↓
主机分配/写入数据 → Runtime 装载与启动 → SimX 执行 → 读回并核对
```

| 检查范围 | 实际结果 |
|---|---|
| 固定版本原生 SimX demo | PASS，输出 `PASSED!`，退出码 0 |
| PTX vadd 编译 | PASS，生成 ELF、vxbin、反汇编；包含 Vortex SIMT 指令 |
| PTX vadd 在 SimX 执行 | **96/96 PASS**：长度边界、不同 block、非零偏移、哨兵与 u32 溢出 |
| 超时恢复 | 实际超时后排空队列、失效旧句柄、重新分配并执行，PASS |
| Linux 回归测试 | **130 通过、14 跳过、0 失败**，跳过原因保留在日志 |
| 本阶段 PTX 的处理器 RTL / XRT AFU / U280 | **NOT_RUN**，未进行 E 分工的独立接收 |

96 组用例是 12 个数组长度 × 4 个 block 大小（1/4/7/16）× 2 套输入。当前基线为 RV64 / 1 core / 4 warps / 4 threads，不能据此认定 block32 已通过。

实际运行环境为本机 **Ubuntu 24.04 WSL、glibc 2.39、G++ 13.3、Python 3.12、CMake 3.31.10**。数字服务器保存代码与证据副本；其 glibc 2.17 不能直接运行本次固定预编译工具链，所以本次结果不是服务器或 FPGA 的执行结果。

## 从哪里看起

| 入口 | 内容 |
|---|---|
| [C 本阶段成果与复现](docs/C_RUNTIME_SIMX_20261110.md) | 实现、实验命令、环境与接收边界 |
| [C 第一批记录](docs/C_RUNTIME_PROGRESS_20261110.md) | 模块包装与启动前检查 |
| [当前状态](docs/STATUS.md) / [项目交接](docs/PROJECT_HANDOFF.md) | 最新进展与历史状态，以顶部新记录为准 |
| [团队分工](docs/RESEARCH_PLAN.md) | A—E 分工与研究安排 |
| [合作接口](docs/COLLABORATION_PROTOCOL.md) | 参数、模块、资源与接收约定 |
| [PTX 子集规范](docs/PTX_COMPATIBILITY_PROFILE.md) | 白名单、语义和限制 |
| [本阶段证据](results/c-runtime-simx-20261110/) | 编译产物、日志、原始输入输出和哈希清单 |

## 获取代码与运行检查

```bash
git clone https://github.com/LiuZeheng123/GPGPU-runtime.git
cd GPGPU-runtime
git submodule update --init upstream/vortex
git -C upstream/vortex submodule update --init third_party/softfloat third_party/ramulator2
python3 -B -m unittest discover -s tests -v
```

Windows 可用 `python` 替换 `python3` 运行宿主 Python 检查；设备编译与 SimX 使用兼容 Linux 环境。单测不等于设备执行；缺少编译器、上游源码或历史材料时，相关测试会跳过。运行原生 ABI 布局检查时，将 `VORTEX_SOURCE` 指向完整的固定 Vortex 源码目录，并提供 `g++`。

### 在已准备的 Linux 环境运行 PTX vadd

先准备固定工具链、Ramulator 依赖以及通过原生 smoke 的 SimX 构建。入口分别是 `scripts/prepare_toolchain.py`、`scripts/native_dependencies.py` 和 `scripts/run_native_smoke.py`，参数可用 `--help` 查看。不同配置使用独立构建目录。

下面假定 `RUN_ROOT` 内已有 `tools/`、`build-native/` 和 `evidence/native/summary.json`，来自本仓库 lock 指定版本及 `configs/native_smoke.json`。请修改路径，且输出目录 `module-vadd`、`build-vadd`、`binding`、`evidence/ptx-vadd` 必须尚不存在。

```bash
export RUN_ROOT=/absolute/path/to/your/linux-workspace
export VORTEX_SOURCE="$PWD/upstream/vortex"

python3 -B scripts/ptx_module.py prepare ptx/samples/vadd_u32.ptx \
  --output "$RUN_ROOT/module-vadd" \
  --hardware configs/native_smoke.json --target-lock configs/target_lock.json
python3 -B scripts/ptx_module.py build "$RUN_ROOT/module-vadd" \
  --vortex-source "$VORTEX_SOURCE" --build-root "$RUN_ROOT/build-vadd" \
  --tooldir "$RUN_ROOT/tools" --target-lock configs/target_lock.json
python3 -B scripts/bind_simx_runtime.py \
  --summary "$RUN_ROOT/evidence/native/summary.json" \
  --hardware configs/native_smoke.json --target-lock configs/target_lock.json \
  --output "$RUN_ROOT/binding"

export VORTEX_DRIVER=simx
export VORTEX_PROFILING=0
export LD_LIBRARY_PATH="$RUN_ROOT/build-native/sw/runtime${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 -B scripts/run_ptx_simx.py \
  --module "$RUN_ROOT/module-vadd" --binding "$RUN_ROOT/binding/binding.json" \
  --target-lock configs/target_lock.json --output "$RUN_ROOT/evidence/ptx-vadd"
```

归档的 binding 包含原执行环境绝对路径和库哈希，**不能直接用于另一台机器**；新环境需重新构建并生成 binding。原环境的复跑方法与完整证据见 [C 实验记录](docs/C_RUNTIME_SIMX_20261110.md)。

## 核心目录

```text
scripts/ptx_frontend.py      PTX 解析、检查与代码生成
scripts/ptx_module.py        设备包装、编译与模块校验
scripts/ptx_launch.py        参数和 buffer 生命周期检查
scripts/ptx_runtime.py       真实 Vortex2 API、队列和资源管理
scripts/bind_simx_runtime.py 构建、配置与动态库身份绑定
scripts/run_ptx_simx.py      实际执行与结果捕获
ptx/samples/                PTX 示例
configs/                    固定版本、ABI 与硬件配置
tests/                      宿主单测和 ABI 检查
docs/                       分工、接口、状态与交接
results/                    按运行编号保存的实验记录
upstream/vortex/            固定上游 Git 子模块
```

`results/c-runtime-simx-20261110/export.json` 保存导出文件的 SHA-256。各 `cases.zip` 保存输入、预期值与读回值，失败尝试也保留。完整 SDK、工具链缓存、动态库和大型 FPGA 产物按固定版本重建，不放入 Git。部分同学历史材料由原工作区保存，详见[历史证据索引](results/README.md)。

## 当前限制与下一步

- Runtime 当前接通 SimX，单队列、单任务在途；本轮按每个 context 一个模块验证。
- 恢复证明的是 SimX 队列排空与资源重建，未证明设备硬复位、故障 abort 或 PCIe/DMA 隔离。
- 下一步增加 copy/affine 的真实 PTX 执行，接收 block32 候选与 E 独立用例，再对接 B 的 U280 平台。
- A/B 历史 FPGA 构建和时序材料为参考成果；HOST 通路、平台约束与板上结果仍按团队最新证据接收。

## 后续保存与同步

个人开发分支为 `c/liuzeheng-runtime`。提交说明改动、命令、结果和验证范围；新实验写入新的 `results/<run_id>/`，不改写旧证据。向团队同步前先对齐共享仓库最新基线，再提交 C 分工的改动供审阅。

仓库只保存项目文件；服务器密码、API key、个人 SSH 配置和工具链缓存不应提交。
