# 11 月 24 日复现团队首期数字系统

在 Ubuntu 24.04 WSL 上独立检出团队标签 [baseline-2026-11-23](https://github.com/slishysun974/Vortex-U280/tree/63e939bfd2c8b4edeb5c0fc51afb1b4e1eb6923e)。从该版 PTX 重新编译了 Iris 最近质心分类器和六个基础算子模块，复用了个人环境已有的三套 Vortex 原生仿真库。应用和测试输入来自团队发布版本，完整命令及退出码随捕获归档。

| 本地新执行 | SimX | 处理器 RTL | AFU RTL |
|---|---:|---:|---:|
| copy、vadd、affine 及其变体 | 48/48 | 48/48 | 48/48 |
| Iris 分类 | 9/9 | 9/9 | 9/9 |

共 171 次功能执行通过。Iris 从原始数据重新生成冻结输入，覆盖空批次、31/32/33 条边界、平局以及正式的 45 条测试样本。距离和类别逐项符合整数参考答案。三个仿真后端与团队公开的 U280 捕获逐字节比较，9 组用例的输入、质心和输出三个缓冲区（包括保护区）共 81 次比较全部相同。45 条样本中分类与真实标签一致 40 条，这是该分类器的准确率。宿主测试 316 项中通过 294 项，跳过 22 项，原因逐项统计在回执中。

本轮沿用 11 月 11 日已构建的仿真库，个人账户的实卡运行继续暂缓。基线校验器另行离线复核同学保存的四路算子记录，并从同卡 422 次历史启动、3,376 次计数器读取中复算 180 对正式计时。六档输入中的最大规模为 65,533 行，对该档得到 PTX / C++ 设备周期比约 1.0339。物理故障恢复与 TIMING-7 仍在团队基线的待办范围内。

[本轮回执](summary.json)记录各后端用例、冻结数据与设备镜像哈希、历史板测输出对照哈希。[原始记录](captures.zip)含执行命令、日志、冻结输入、新模块、捕获和仿真库绑定。压缩包的 SHA-256 可在回执的 `archive_file` 查到。

## 复核方法

普通电脑只需要 Git 和 Python 3.10 或以上版本即可复核公开记录：

```sh
git clone --depth 1 --branch baseline-2026-11-23 https://github.com/slishysun974/Vortex-U280.git
cd Vortex-U280
python -B scripts/review_baseline.py
```

要重新执行本轮全部仿真，使用[运行脚本](reproduce.py)。先准备固定的 Vortex 源码、配套的工具链、可用的 CMake，以及三个已构建并在本机绑定的原生模型。绑定父目录下应有 `binding-simx-v1/`、`binding-rtlsim-v1/`、`binding-xrtsim-v1/`，每份绑定引用本机实际的库和构建回执。将下例中的变量换成本机目录。输出目录须为新目录。

```sh
python3 -B "$PERSONAL_REPO/results/c-baseline-verification-20261124-v1/reproduce.py" \
  --source "$BASELINE_REPO" --vortex "$VORTEX_SOURCE" --tools "$TOOLDIR" \
  --bindings "$BINDINGS_ROOT" --out "$NEW_RUN"
```

脚本把宿主测试、公开记录复核和新执行的结果写入 `$NEW_RUN/evidence/summary.json`。逐字节对照可取 `$NEW_RUN/iris-{simx,rtlsim,xrtsim}/<case>/{x,sums,out}.after.bin`，分别与团队仓库 `results/iris-board-20261123-v1/returned/iris-board-20261123-v1/u280-xrt/` 中对应文件比较。
