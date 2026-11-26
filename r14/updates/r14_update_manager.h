// SPDX-License-Identifier: GPL-3.0-or-later
// HIMURA R14: safe, non-blocking NSP update/DLC import from USB.
// Copies intact PFS0 NSPs to the Orbis Eden external-content directory.
// TitleID compatibility is checked by the Eden loader only when a game boots.
#pragma once
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace Himura::Updates {
struct Package {
    std::filesystem::path path;
    std::string source;
    std::uint64_t size{};
};
std::vector<Package> Discover();
class Importer {
public:
    Importer() = default;
    Importer(const Importer&) = delete;
    Importer& operator=(const Importer&) = delete;
    ~Importer();
    bool Start(const Package& package);
    bool Tick();  // bounded copy (256 KiB); returns true if display should refresh
    void Cancel();
    bool Active() const { return active_; }
    unsigned Percent() const;
    const std::string& Message() const { return message_; }
    std::uint64_t Copied() const { return copied_; }
    std::uint64_t Total() const { return total_; }
private:
    std::ifstream in_;
    std::ofstream out_;
    std::filesystem::path tmp_;
    std::filesystem::path destination_;
    std::vector<char> buffer_{std::vector<char>(256 * 1024)};
    std::string message_{"Selecione um NSP de update ou DLC no USB"};
    std::uint64_t copied_{}, total_{};
    bool active_{false};
    void Fail(const std::string& message);
};
}
