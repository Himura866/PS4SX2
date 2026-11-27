#!/usr/bin/env python3
"""Tests for the PS4-specific Vulkan safety patch (no emulator build needed)."""
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "r13_radv", Path(__file__).with_name("patch-r13-ps4-radv-safe-path.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

sample_macro = """
void HLE_MultiDrawIndexedIndirectCount::Execute() {
    const auto topology = Maxwell3D::Regs::PrimitiveTopology(parameters[2]);
    if (IsTopologySafe(topology)) {
        const u32 start_indirect = parameters[0];
    }
}
"""
sample_device = """
    logical = vk::Device::Create(physical, queue_cis, ExtensionListForVulkan(loaded_extensions), first_next, dld);
"""
new_macro, new_device = mod.patch_text(sample_macro, sample_device)
assert "#ifdef __OPENORBIS__" in new_macro
assert "Fallback(system, maxwell3d, parameters);\n    return;" in new_macro
assert "#ifdef __OPENORBIS__" in new_device
assert "RemoveExtension(extensions.conditional_rendering" in new_device
assert "RemoveExtension(extensions.draw_indirect_count" in new_device
assert new_macro.count("if (IsTopologySafe(topology)) {") == 1
assert new_device.count("logical = vk::Device::Create") == 1

for source in [new_macro, sample_macro.replace("if (IsTopologySafe(topology))", "if (true)")]:
    try:
        mod.patch_text(source, sample_device)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Applied twice or changed source should fail closed")
try:
    mod.patch_text(sample_macro, "missing Vulkan anchor")
except RuntimeError:
    pass
else:
    raise AssertionError("Changed Vulkan source should fail closed")
print("PASS R13 RADV: PS4-only guard, fallback, idempotence and missing-anchor refusal")
