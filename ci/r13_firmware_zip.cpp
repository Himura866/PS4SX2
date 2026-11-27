// HIMURA SWITCH R13 - safe, streaming ZIP firmware importer for OpenOrbis.
// ZIP stored/deflate only, CRC32 verified, protects pre-existing NAND content.
// No copyrighted firmware or keys bundled.
#include "yuzu_ps4/r13_firmware_zip.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <functional>
#include <limits>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
#include <zlib.h>
#ifndef R13_FIRMWARE_DATA_ROOT
#define R13_FIRMWARE_DATA_ROOT "/data/EdenPS4"
#endif

namespace HimuraFirmware {
namespace {
uint16_t U16(const unsigned char* p) { return uint16_t(p[0]) | (uint16_t(p[1])<<8); }
uint32_t U32(const unsigned char* p) { return uint32_t(U16(p)) | (uint32_t(U16(p+2))<<16); }
struct Entry { std::string name; uint32_t offset{}, packed{}, length{}, crc{}; uint16_t method{}; };
bool Read(FILE* f, void* data, size_t len) { return len==0 || fread(data,1,len,f)==len; }
bool At(FILE* f, uint64_t offset) {
    return offset<=uint64_t(std::numeric_limits<long>::max()) && fseek(f,long(offset),SEEK_SET)==0;
}
std::string BaseName(const std::string& s) {
    const size_t pos=s.find_last_of('/');
    return pos==std::string::npos?s:s.substr(pos+1);
}
bool NameAllowed(const std::string& s) {
    if (s.empty() || s[0]=='/' || s.find('\\')!=std::string::npos ||
        s.find(':')!=std::string::npos || s.find('\0')!=std::string::npos) return false;
    const std::string clean=s.back()=='/'?s.substr(0,s.size()-1):s;
    if(clean.empty())return false;
    size_t start=0;
    while(start<clean.size()){
        size_t end=clean.find('/',start); if(end==std::string::npos) end=clean.size();
        const std::string part=clean.substr(start,end-start);
        if(part.empty() || part=="." || part=="..") return false;
        start=end+1;
    }
    return true;
}
bool FirmwareName(const std::string& path) {
    const std::string name=BaseName(path);
    if(name.size()<5 || name.size()>110 || name.substr(name.size()-4)!=".nca")return false;
    for(const unsigned char c:name)
        if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||
             (c>='0'&&c<='9')||c=='_'||c=='-'||c=='.')) return false;
    return true;
}
bool MkdirIfMissing(const char* path) {
    if(mkdir(path,0777)==0) return true;
    struct stat st{};
    return stat(path,&st)==0 && S_ISDIR(st.st_mode);
}
bool Extract(FILE* f,const Entry& e,const std::string& dest) {
    unsigned char local[30];
    if(!At(f,e.offset) || !Read(f,local,sizeof local) || U32(local)!=0x04034b50u)
        return false;
    const uint16_t flags=U16(local+6),method=U16(local+8);
    if((flags&1)!=0 || method!=e.method) return false;
    const uint64_t data_offset=uint64_t(e.offset)+30+U16(local+26)+U16(local+28);
    if(!At(f,data_offset))return false;
    FILE* out=fopen(dest.c_str(),"wb");
    if(!out)return false;
    std::array<unsigned char,65536> in{},buffer{};
    uint64_t remaining=e.packed, produced=0;
    uLong checksum=crc32(0,Z_NULL,0);
    bool ok=true,finished=e.method==0;
    z_stream strm{};
    if(e.method==8 && inflateInit2(&strm,-MAX_WBITS)!=Z_OK)ok=false;
    while(ok && remaining>0) {
        const size_t n=size_t(std::min<uint64_t>(remaining,in.size()));
        if(!Read(f,in.data(),n)) {ok=false;break;}
        remaining-=n;
        if(e.method==0) {
            if(produced+n>e.length || fwrite(in.data(),1,n,out)!=n){ok=false;break;}
            checksum=crc32(checksum,in.data(),uInt(n)); produced+=n;
            continue;
        }
        strm.next_in=in.data(); strm.avail_in=uInt(n);
        while(ok && strm.avail_in>0 && !finished) {
            strm.next_out=buffer.data(); strm.avail_out=uInt(buffer.size());
            const int status=inflate(&strm,Z_NO_FLUSH);
            const size_t count=buffer.size()-strm.avail_out;
            if(produced+count>e.length || (count && fwrite(buffer.data(),1,count,out)!=count)){
                ok=false;break;
            }
            if(count) checksum=crc32(checksum,buffer.data(),uInt(count));
            produced+=count;
            if(status==Z_STREAM_END){finished=true;if(strm.avail_in || remaining)ok=false;}
            else if(status!=Z_OK || (count==0 && strm.avail_in==0 && remaining==0)) ok=false;
        }
        if(finished && remaining)ok=false;
    }
    if(e.method==8)inflateEnd(&strm);
    if(fflush(out)!=0 || fsync(fileno(out))!=0)ok=false;
    if(fclose(out)!=0)ok=false;
    if(!ok || !finished || produced!=e.length || uint32_t(checksum)!=e.crc){
        unlink(dest.c_str());
        return false;
    }
    return true;
}
bool Parse(FILE* f,std::vector<Entry>& entries,std::string& reason){
    if(fseek(f,0,SEEK_END)!=0){reason="ZIP sem tamanho legivel";return false;}
    const long end=ftell(f);
    if(end<22){reason="ZIP incompleto";return false;}
    const size_t tail_size=size_t(std::min<long>(end,65557));
    std::vector<unsigned char> tail(tail_size);
    if(!At(f,uint64_t(end)-tail_size)||!Read(f,tail.data(),tail.size())){
        reason="Falha de leitura ZIP";return false;
    }
    size_t pos=tail_size;
    for(size_t p=tail_size-22;;--p){
        if(U32(tail.data()+p)==0x06054b50u && p+22+U16(tail.data()+p+20)==tail_size){
            pos=p;break;
        }
        if(p==0)break;
    }
    if(pos==tail_size){reason="Diretorio central ZIP ausente";return false;}
    const unsigned char* eocd=tail.data()+pos;
    const uint16_t count=U16(eocd+10), disk=U16(eocd+4);
    const uint32_t dir_len=U32(eocd+12),dir_offset=U32(eocd+16);
    if(disk || U16(eocd+6) || count!=U16(eocd+8) || count==0 ||
       count>4096 || count==0xffff || dir_offset==0xffffffffu ||
       dir_len==0xffffffffu || dir_len>(8u<<20) ||
       uint64_t(dir_offset)+dir_len>uint64_t(end)){
        reason="ZIP multidisco, ZIP64 ou estrutura invalida";return false;
    }
    std::vector<unsigned char> dir(dir_len);
    if(!At(f,dir_offset)||!Read(f,dir.data(),dir.size())){
        reason="Falha ao ler indices do ZIP";return false;
    }
    size_t cur=0;
    uint64_t total=0;
    for(unsigned i=0;i<count;++i){
        if(cur+46>dir.size()||U32(dir.data()+cur)!=0x02014b50u){
            reason="Indice ZIP corrompido";return false;
        }
        const unsigned char* c=dir.data()+cur;
        const uint16_t flags=U16(c+8), method=U16(c+10);
        const uint32_t packed=U32(c+20),length=U32(c+24),offset=U32(c+42);
        const size_t name_len=U16(c+28), extra=U16(c+30), comment=U16(c+32);
        const size_t next=cur+46+name_len+extra+comment;
        if(next>dir.size()){reason="Nome ZIP invalido";return false;}
        const std::string name(reinterpret_cast<const char*>(c+46),name_len);
        if((flags&1) || (flags&0x40) || packed==0xffffffffu || length==0xffffffffu ||
           offset==0xffffffffu || (method!=0&&method!=8) ||
           !NameAllowed(name)){
            reason="Entrada ZIP nao suportada/insegura";return false;
        }
        if(FirmwareName(name)){
            if(length<0x400 || length>(1u<<30) || packed==0 ||
               (method==0 && length!=packed)){
                reason="Arquivo NCA ZIP invalido ou muito grande";return false;
            }
            total+=length;
            if(total>(3ull<<30)){reason="Firmware ZIP excede 3 GiB";return false;}
            const std::string base=BaseName(name);
            for(const Entry& other:entries)if(other.name==base){
                reason="NCAs duplicados no ZIP";return false;
            }
            entries.push_back({base,offset,packed,length,U32(c+16),method});
        }
        cur=next;
    }
    if(entries.empty()){reason="ZIP nao contem arquivos .nca validos";return false;}
    return true;
}
}
std::string InstallZip(const std::string& path,
                       const std::function<void(size_t,size_t)>& progress){
    if(path.rfind("/mnt/usb",0)!=0 && path.rfind(R13_FIRMWARE_DATA_ROOT "/",0)!=0)
        return "Origem ZIP nao autorizada";
    FILE* f=fopen(path.c_str(),"rb");
    if(!f)return "Nao foi possivel abrir o firmware ZIP";
    std::vector<Entry> entries; std::string reason;
    bool parsed=Parse(f,entries,reason);
    if(!parsed){fclose(f);return reason;}
    const std::string pending=R13_FIRMWARE_DATA_ROOT "/firmware-pending-"+std::to_string(getpid());
    if(mkdir(pending.c_str(),0700)!=0){fclose(f);return "Pasta temporaria indisponivel";}
    std::vector<std::string> temporary;
    bool ok=true;
    for(const Entry& entry:entries){
        const std::string target=pending+"/"+entry.name;
        if(!Extract(f,entry,target)){reason="NCA invalido ou CRC incorreto: "+entry.name;ok=false;break;}
        temporary.push_back(target);
        if(progress)progress(temporary.size(),entries.size());
    }
    fclose(f);
    const char* nand=R13_FIRMWARE_DATA_ROOT "/nand";
    const char* sys=R13_FIRMWARE_DATA_ROOT "/nand/system";
    const char* contents=R13_FIRMWARE_DATA_ROOT "/nand/system/Contents";
    const char* registered=R13_FIRMWARE_DATA_ROOT "/nand/system/Contents/registered";
    if(ok && !(MkdirIfMissing(nand)&&MkdirIfMissing(sys)&&
               MkdirIfMissing(contents)&&MkdirIfMissing(registered))){
        reason="Pasta NAND nao esta gravavel";ok=false;
    }
    // Never overwrite a user's prior firmware, installed update or DLC.
    if(ok)for(const Entry& entry:entries){
        const std::string dest=std::string(registered)+"/"+entry.name;
        struct stat st{};
        if(lstat(dest.c_str(),&st)==0){reason="NCA ja existe: "+entry.name;ok=false;break;}
    }
    std::vector<std::string> committed;
    if(ok)for(const Entry& entry:entries){
        const std::string dest=std::string(registered)+"/"+entry.name;
        const std::string src=pending+"/"+entry.name;
        if(rename(src.c_str(),dest.c_str())!=0){
            reason="Falha ao gravar NCA na NAND";ok=false;break;
        }
        committed.push_back(dest);
    }
    if(!ok)for(const std::string& s:committed)unlink(s.c_str());
    for(const std::string& s:temporary)unlink(s.c_str());
    rmdir(pending.c_str());
    if(!ok)return reason+"; dados anteriores preservados";
    return "Firmware ZIP instalado: "+std::to_string(entries.size())+
           " arquivos NCA. Reinicie o emulador para aplicar.";
}
} // namespace HimuraFirmware
