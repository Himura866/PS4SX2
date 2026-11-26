// SPDX-License-Identifier: GPL-3.0-or-later
#include "menu/r14_update_manager.h"
#include "ps4_platform.h"
#include <algorithm>
#include <cctype>
#include <set>
#include <system_error>
#include <utility>

namespace Himura::Updates {
namespace fs = std::filesystem;

static bool IsNsp(const fs::path& file) {
    std::string ext = file.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return std::tolower(c); });
    return ext == ".nsp" && !file.filename().string().starts_with('.');
}

std::vector<Package> Discover() {
    std::vector<Package> candidates;
    std::set<std::string> seen;
    for (int n = 0; n < 8 && candidates.size() < 128; ++n) {
        const auto root = fs::path{"/mnt/usb" + std::to_string(n)};
        for (const auto& folder : {"updates", "Updates", "UPDATES", "dlc", "DLC",
                                   "switch/updates", "switch/dlc"}) {
            const fs::path dir = root / folder;
            std::error_code ec;
            for (fs::directory_iterator it{dir, ec}, end;
                 !ec && it != end && candidates.size() < 128; it.increment(ec)) {
                const auto file = it->path();
                std::error_code e2;
                if (!it->is_regular_file(e2) || !IsNsp(file)) continue;
                const auto size = it->file_size(e2);
                if (e2 || size < 4) continue;
                if (!seen.insert(file.string()).second) continue;
                candidates.push_back({file, "USB" + std::to_string(n), size});
            }
        }
    }
    std::sort(candidates.begin(), candidates.end(), [](const Package& a, const Package& b) {
        return a.path.string() < b.path.string();
    });
    Ps4::Log("HIMURA R14 content manager: %zu USB NSP candidates", candidates.size());
    return candidates;
}

Importer::~Importer() { Cancel(); }

void Importer::Fail(const std::string& message) {
    in_.close();
    out_.close();
    std::error_code ec;
    if (!tmp_.empty()) fs::remove(tmp_, ec);
    active_ = false;
    message_ = message;
    Ps4::Log("HIMURA R14 update/DLC import: %s", message.c_str());
}

bool Importer::Start(const Package& package) {
    if (active_) return false;
    copied_ = 0;
    total_ = package.size;
    in_.open(package.path, std::ios::binary);
    if (!in_) { Fail("Erro: nao foi possivel abrir o NSP"); return false; }
    char magic[4] = {};
    in_.read(magic, 4);
    if (in_.gcount() != 4 || std::string(magic, 4) != "PFS0") {
        Fail("NSP invalido: cabecalho PFS0 ausente");
        return false;
    }
    in_.clear();
    in_.seekg(0);
    const fs::path folder = fs::path{Ps4::DataDir} / "updates";
    std::error_code ec;
    fs::create_directories(folder, ec);
    if (ec) { Fail("Erro: sem acesso a pasta de updates"); return false; }
    destination_ = folder / package.path.filename();
    if (fs::exists(destination_, ec)) {
        if (!ec && fs::file_size(destination_, ec) == total_ && !ec) {
            Fail("NSP ja esta na pasta de updates");
        } else {
            Fail("Existe NSP com mesmo nome; nenhuma substituicao automatica");
        }
        return false;
    }
    tmp_ = destination_;
    tmp_ += ".himura-import.part";
    fs::remove(tmp_, ec);  // Only this app's known temp file, never an installed NSP.
    out_.open(tmp_, std::ios::binary | std::ios::trunc);
    if (!out_) { Fail("Erro: nao foi possivel criar arquivo temporario"); return false; }
    active_ = true;
    message_ = "Importando NSP de update/DLC...";
    Ps4::Log("HIMURA R14 content import begin: %s (%llu bytes)",
             package.path.string().c_str(), static_cast<unsigned long long>(total_));
    return true;
}

unsigned Importer::Percent() const {
    return total_ ? static_cast<unsigned>(std::min<std::uint64_t>(100, copied_ * 100 / total_)) : 0;
}

bool Importer::Tick() {
    if (!active_) return false;
    const auto remaining = total_ - copied_;
    const auto amount = static_cast<std::streamsize>(
        std::min<std::uint64_t>(remaining, buffer_.size()));
    if (amount > 0) {
        in_.read(buffer_.data(), amount);
        if (in_.gcount() != amount) {
            Fail("Erro de leitura do USB: importacao cancelada");
            return true;
        }
        out_.write(buffer_.data(), amount);
        if (!out_) {
            Fail("Sem espaco ou erro de escrita: importacao cancelada");
            return true;
        }
        copied_ += static_cast<std::uint64_t>(amount);
    }
    if (copied_ == total_) {
        out_.flush();
        if (!out_) { Fail("Erro ao finalizar arquivo temporario"); return true; }
        out_.close();
        if (out_.fail()) { Fail("Erro ao fechar arquivo temporario"); return true; }
        in_.close();
        std::error_code ec;
        fs::rename(tmp_, destination_, ec);
        if (ec) {
            Fail("Erro ao registrar NSP: sem mudar jogo/saves");
            return true;
        }
        active_ = false;
        message_ = "NSP importado! Sera reconhecido se corresponder ao jogo.";
        Ps4::Log("HIMURA R14 content copied: %s; Eden will verify matching TitleID at boot",
                 destination_.string().c_str());
    }
    return true;
}

void Importer::Cancel() {
    if (active_) Fail("Importacao cancelada pelo usuario");
}
}
