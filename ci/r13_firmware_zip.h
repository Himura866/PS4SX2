#pragma once
#include <cstddef>
#include <functional>
#include <string>
namespace HimuraFirmware {
// Streaming ZIP firmware installer; never deletes/overwrites existing NAND files.
// Progress callback counts verified .nca entries, not simulated percentages.
std::string InstallZip(const std::string& path, const std::function<void(size_t,size_t)>& progress);
}
