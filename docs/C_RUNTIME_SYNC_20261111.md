# C 第五批：同步团队 Runtime 与本地复现

日期：2026-11-11。同步来源为 [slishysun974/Vortex-U280 @ 2aad3a0](https://github.com/slishysun974/Vortex-U280/tree/2aad3a0e01cf1a28cd08df854982f5bf8b698807)。本批工作是接回同学已整合的 Runtime 改动、补齐公开测试材料并在本人 WSL 重跑；**本人账户的 U280 实板复现按用户要求暂缓（DEFERRED_BY_USER）**。

## 同步内容与归属

上游已经整合本人 `LiuZeheng123/GPGPU-runtime` 的 `7f3575db67888c03d1c2c4dc3743051c735519dd`，并增加 U280 适配、Python 3.6 兼容、E 冻结语料与故障处理修正。本仓库接回这些改动，保留本人原来的三路仿真批量入口及历史结果，不将同学的板上执行或验收工作记为本人新执行。

- 生产代码、相关配置和测试按固定上游快照原样同步，路径/前后哈希见 [import.json](../results/c-upstream-sync-20261111-v1/import.json)。完整公开快照 ZIP 校验了 **1934 个 Git blob**；ZIP SHA-256 为 `dc30752988a4e4f512ce1ebbd1a84fde586efb92f6fc0909705e647faca1b1a3`。
- `ptx_frontend.py` 保留上游旧前端入口；C 模块使用 **`ptx_frontend_v12.py`**，不能根据旧文件名误判为回退。
- 新增 `ptx_u280.py`、板上绑定/执行入口、`ptx-vx-module-u280-v2-draft` 模块支持。实际运行仍需匹配的板卡、xclbin、运行库及身份检查。
- 接回 **sticky-device-fault-v1**：非超时原生故障被持续记录，重复恢复不能误报成功；超时恢复同时要求队列排空和原始启动事件成功。物理后端的恢复仍返回 `E_UNAVAILABLE`，不宣称硬复位或 DMA 隔离。
- `configs/acceptance/` 的输入、答案和冻结 manifest 原样导入。另补齐旧 E15 测试依赖的 45 个原始输入文件与来源收据；既有文件不覆盖，冻结答案不改写。
- 上游详细说明与原始记录收录在 [upstream-public-snapshot.zip](../results/c-upstream-sync-20261111-v1/upstream-public-snapshot.zip)，包括 `docs/C_RUNTIME_MERGE.md`、`docs/E_RUNTIME_UNSEEN_ACCEPTANCE.md`、`docs/RUNTIME_RECOVERY_20261111.md` 和服务器指引。

## 本人本轮实际验证

环境：Ubuntu 24.04 WSL / Python 3.12；固定 Vortex `7fe19369587c087f902c3e2bc2add612aa910a95` 与工具链 `8c64cf921d3c6c456e80f00d24482d0aa2153a82`。复用上一批已验证的三套独立 native 构建与 binding，重新编译六个 PTX 模块。原生模型为 SimX、处理器 RTL 与 NOXRT/XRTSIM AFU，不是实板或厂商 hw_emu。

| 检查 | 本轮结果 |
|---|---|
| Linux 宿主回归 | 269 项：**247 通过，22 跳过，0 失败** |
| 冻结 PTX 模块重新准备/编译 | copy、vadd、affine 及各自 variant，**6/6 PASS** |
| E 冻结语料在三个仿真后端重新运行 | **每路 48/48，共 144/144 PASS** |
| 每路 Runtime 生命周期 | 一个 context，41 次模块装载，2 代 buffer；144 份完整数组核对 |
| 超时/故障回归 | 三后端各 timeout、cp-fault、canary，**9/9 worker PASS** |
| 上游四路历史捕获离线复核 | SimX / RTL / AFU / U280 各 48 项，四路 checker 均 PASS；不是本轮设备执行 |
| 本人账户 U280 执行 | **NOT_RUN / DEFERRED_BY_USER** |

timeout 每路实际执行两次超时、排空、旧句柄拒绝和恢复后计算，共六个恢复循环。cp-fault 每路验证真实仿真原生错误持续锁定、资源保持且不允许重复恢复；canary 每路在新进程验证正常计算。这些检查不证明物理设备故障恢复。

22 项跳过分别涉及：物理 D10/D12 二进制 4 项、Windows 专属检查 1 项、历史 D8 RTL 包 9 项、历史板上/AFU 捕获 4 项、历史 Runtime 输入 1 项、D8 配置 1 项、测试默认位置的固定源码子模块 1 项、Vivado 报告 1 项。完整理由见 [单测日志](../results/c-upstream-sync-20261111-v1/unittests.log)。ABI 核验通过 `VORTEX_SOURCE` 指向本机隔离固定源码；另一个 GCC9 测试只检查默认子模块位置，因此仍跳过。

首次尝试因缺少上述旧输入及来源收据失败（7 errors / 22 skipped）；补齐上游原件后在新目录 `gpgpu-c-sync-20261111-v2` 重跑通过。首次失败日志和最终成功日志均归档，未放宽断言。

冻结 manifest SHA-256 为 `ee47fa9d641a1c94f35666610d4910924c233fb83f13b1e859c26ce3de95a654`。这是**本人对上游 E 语料的复现**；原 checker 输出里的 independent E 描述语料来源，不代表本次获得新的非作者或人类 E 签署。上游记录中的独立 E 为独立 AI 上下文，人工接收仍需团队确认。

## 复核与重新运行

所有命令、退出码、耗时和源文件 SHA-256 见 [summary.json](../results/c-upstream-sync-20261111-v1/summary.json)。原始输入输出、模块、绑定、首轮失败与最终日志保存在 [personal-validation.zip](../results/c-upstream-sync-20261111-v1/personal-validation.zip)，逐文件哈希见 [export.json](../results/c-upstream-sync-20261111-v1/export.json)。

只复核本轮归档，不启动设备（`/tmp/c-sync-review` 应为新目录）：

```bash
python3 -m zipfile -e results/c-upstream-sync-20261111-v1/personal-validation.zip /tmp/c-sync-review
for backend in simx rtlsim xrtsim; do
  python3 -B scripts/e_acceptance/runtime_unseen_check.py \
  \
  --corpus configs/acceptance/e-runtime-unseen-20261111-v1 \
  \
  --run /tmp/c-sync-review/attempt-v2/evidence/$backend \
  \
  --out /tmp/c-sync-review/$backend-checked.json
done
```

在已具备固定工具链、三套 native 构建和新生成 binding 的 Linux 环境重新执行：先用 `scripts/ptx_module.py prepare/build` 为冻结语料 `sources/` 下六个 PTX 建立同名模块目录，统一使用 `configs/candidates/block32-v1/` 的硬件配置和 lock。完整实例命令见 summary；其本机路径需替换，归档 binding 不可直接移植。

```bash
# MODULES 内应有 copy、copy_variant、vadd、vadd_variant、affine、affine_variant。
# BINDING 指向当前 backend 的新绑定；RUN_OUT 必须不存在。
# VORTEX_DRIVER 和 LD_LIBRARY_PATH 使用该 binding 内对应的 driver 与 library_dir。
python3 -B scripts/e_acceptance/runtime_unseen_run.py \
  --corpus configs/acceptance/e-runtime-unseen-20261111-v1 \
  --modules "$MODULES" --binding "$BINDING" \
  --target-lock configs/candidates/block32-v1/target_lock.json \
  --backend "$BACKEND" --out "$RUN_OUT"
python3 -B scripts/e_acceptance/runtime_unseen_check.py \
  --corpus configs/acceptance/e-runtime-unseen-20261111-v1 \
  --run "$RUN_OUT" --out "$RUN_OUT-checked.json"
```

`BACKEND` 分别为 simx、rtlsim、xrtsim；xrtsim 的原生 driver 是 xrt，须以 binding 为准。故障验证只在仿真中使用 `validate_runtime_recovery.py --worker`，具体九条调用见 summary，不将它用于物理卡。

## 后续交接

现在无需用户补充材料。代码同步、本地验证和个人仓库归档已完成；实板在以后继续。届时只需同学提供本人能读取的匹配文件共享路径：**vortex_afu.xclbin、libvortex.so、libvortex-xrt.so**，并确认对应构建身份和可用时间。已有上游哈希/配置可用于核对，无需重新要求同学开发一套 Runtime。

按团队安排优先 B1，避开 B2/B5/3E；卡状态须在实际操作前重新检查。此次不加载、不复位、不进行物理故障注入。TIMING-7 仍 OPEN；上游正常功能通过不能替代时序问题关闭、硬件恢复验证或人工 E 接收。

D 后续交付新的 PTX/语义能力时提供固定源码与预期结果，C 继续验证模块打包/运行；E 可使用冻结语料、checker 与本轮原始捕获复核并记录自己的接收结论。个人仓库上传不自动更新团队共享仓库。
