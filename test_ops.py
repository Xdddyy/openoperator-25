#!/usr/bin/env python3
"""
Cambricon MLU370 BANG C 算子本地测试脚本

用法:
    python3 test_ops.py              # 测试 config 中列出的所有题目
    python3 test_ops.py --all        # 测试所有 .mlu 文件
    python3 test_ops.py LeakyReLU    # 测试指定算子

依赖: torch, torch_mlu (寒武纪定制版)
"""

import sys
import time
import argparse
import pathlib

import torch

try:
    import torch_mlu  # noqa: F401
except ImportError:
    print("ERROR: torch_mlu 未安装。请先安装寒武纪版 PyTorch 和 torch_mlu。")
    sys.exit(1)

if torch.mlu.device_count() == 0:
    print("ERROR: 未检测到 MLU 设备。请在 MLU370 服务器上运行此脚本。")
    sys.exit(1)

print(f"MLU device: {torch.mlu.get_device_name(0)}")


# ============================================================
# 算子注册表: name -> (mlu_file, arg_names, ref_fn, shape, extra_kwargs)
# ============================================================
OPS_META = {
    "LeakyReLU": {
        "file": "LeakyReLU.mlu",
        "args": ["input", "negative_slope"],
        "ref": lambda x, ns=0.01: torch.nn.functional.leaky_relu(x, ns),
        "shape": (1024, 256),
        "extra": {"negative_slope": 0.01},
    },
    "Sqrt": {
        "file": "070_Sqrt.mlu",
        "args": ["x"],
        "ref": lambda x: torch.sqrt(torch.abs(x)),
        "shape": (1024, 256),
        "extra": {},
    },
    "MSE_Loss": {
        "file": "103_MSE_Loss.mlu",
        "args": ["predictions", "targets"],
        "ref": lambda pred, targ: torch.nn.functional.mse_loss(pred, targ),
        "shape": (1024, 256),
        "extra": {},
    },
}

# config 中三位编号 -> 算子名的映射
NUM_TO_NAME = {
    "001": "LeakyReLU",
    "070": "Sqrt",
    "103": "MSE_Loss",
}


def compile_and_load(mlu_path):
    """编译 .mlu 文件并加载为 Python 模块"""
    from torch.utils.cpp_extension import load

    mlu_path = pathlib.Path(mlu_path)
    module = load(
        name=f"bang_{mlu_path.stem}",
        sources=[str(mlu_path)],
        verbose=False,
    )
    if not hasattr(module, "bang_func"):
        raise RuntimeError(f"编译成功但模块中未找到 bang_func")
    return module


def test_operator(name, meta, device="mlu"):
    """测试单个算子的正确性和性能"""
    print(f"\n{'='*60}")
    print(f"  测试: {name}")
    print(f"  文件: {meta['file']}")
    print(f"{'='*60}")

    shape = meta["shape"]
    extra = meta.get("extra", {})
    ref_fn = meta["ref"]
    args = meta["args"]

    mlu_path = pathlib.Path(meta["file"])
    if not mlu_path.exists():
        print(f"  SKIP: {mlu_path} 不存在")
        return False

    print(f"  编译加载 {mlu_path} ...")
    try:
        module = compile_and_load(mlu_path)
    except Exception as e:
        print(f"  FAIL: 编译失败 - {e}")
        return False

    # 生成测试数据
    torch.manual_seed(42)
    inputs_cpu = [torch.randn(*shape) for _ in range(len(args) - len(extra))]
    inputs_mlu = [t.to(device) for t in inputs_cpu]

    # 运行 MLU kernel（预热 + 计时）
    bang_func = module.bang_func
    with torch.no_grad():
        for _ in range(3):
            bang_func(*inputs_mlu, **extra)
        torch.mlu.synchronize()

        N_ITER = 100
        t0 = time.perf_counter()
        for _ in range(N_ITER):
            result_mlu = bang_func(*inputs_mlu, **extra)
        torch.mlu.synchronize()
        mlu_time_ms = (time.perf_counter() - t0) / N_ITER * 1000

    # 运行 PyTorch CPU 参考
    result_mlu_cpu = result_mlu.cpu()
    with torch.no_grad():
        t0 = time.perf_counter()
        for _ in range(N_ITER):
            result_ref = ref_fn(*inputs_cpu, **extra)
        torch_time_ms = (time.perf_counter() - t0) / N_ITER * 1000

    # 精度对比
    if isinstance(result_ref, torch.Tensor) and result_ref.numel() > 0:
        diff = (result_mlu_cpu.float() - result_ref.float()).abs().max().item()
        atol = 1e-2
        ok = diff <= atol
        status = "PASS" if ok else "FAIL (精度超标)"
        print(f"  精度: max_diff={diff:.6f}  (atol={atol})  [{status}]")
    else:
        ok = True
        print(f"  精度: 参考输出为空，跳过对比")

    # 性能对比
    if torch_time_ms > 0:
        speedup = torch_time_ms / mlu_time_ms if mlu_time_ms > 0 else float("inf")
        print(f"  性能: MLU={mlu_time_ms:.4f}ms  CPU={torch_time_ms:.4f}ms  "
              f"speedup={speedup:.2f}x")

    return ok


def get_targets_from_config():
    """从 config 文件读取要测试的题目（三位编号）"""
    config_path = pathlib.Path("config")
    if not config_path.exists():
        return None
    targets = []
    for line in config_path.read_text().strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            targets.append(line)
    return targets


def resolve_ops(targets):
    """将题目标识（名称或三位编号）解析为 (op_name, meta) 列表"""
    selected = []
    for t in targets:
        matched = False
        # 1) 按 config 编号映射
        mapped = NUM_TO_NAME.get(t)
        if mapped and mapped in OPS_META:
            selected.append((mapped, OPS_META[mapped]))
            matched = True
        # 2) 直接按名称匹配
        for op_name, meta in OPS_META.items():
            if t == op_name:
                if not matched:
                    selected.append((op_name, meta))
                matched = True
                break
            file_stem = pathlib.Path(meta["file"]).stem
            if t == file_stem or file_stem.startswith(t):
                if not matched:
                    selected.append((op_name, meta))
                matched = True
                break
        if not matched:
            print(f"WARNING: 未找到算子 '{t}'")
    return selected


def main():
    parser = argparse.ArgumentParser(description="MLU370 BANG C 算子测试")
    parser.add_argument("ops", nargs="*", help="要测试的算子名称或 config 编号")
    parser.add_argument("--all", action="store_true", help="测试所有算子")
    args = parser.parse_args()

    if args.ops:
        targets = args.ops
    elif args.all:
        targets = list(OPS_META.keys())
    else:
        config_targets = get_targets_from_config()
        if config_targets is None or len(config_targets) == 0:
            targets = list(OPS_META.keys())
        else:
            targets = config_targets

    selected = resolve_ops(targets)

    if not selected:
        print("没有要测试的算子。")
        sys.exit(1)

    print(f"将测试 {len(selected)} 个算子: {[s[0] for s in selected]}")

    passed = 0
    failed = 0
    for name, meta in selected:
        try:
            ok = test_operator(name, meta)
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  结果: {passed} passed, {failed} failed, {len(selected)} total")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
