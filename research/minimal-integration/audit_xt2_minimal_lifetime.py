"""Audit fixed minimal carriers against native section/overlay/heap ownership.

Requires local extracted X-T2 4.41 and firmware_analysis (capstone). Static
coverage only: computed pointers, arbitrary DMA and physical retention are not
proved by an empty reference inventory. Original Codex-assisted research.
"""
import hashlib,json,struct
from pathlib import Path
from firmware_analysis import Firmware
ROOT=Path.cwd()  # Run from a locally supplied research workspace.
SPANS={"data":(0x781000,0x784000),"code":(0xdf7900,0xdf8000)}
def overlap(a,b,c,d):return max(a,c)<min(b,d)
def main():
 f=Firmware("xt2-4.41",True)
 image=(ROOT/"firmware/research/eterna-minimal-protected-unverified/ffboot.bin").read_bytes()
 assert hashlib.sha256(image).hexdigest()=="0b92b7922acbe18216996be3808734f50a6d66558b520aa327d56b7bc0ef23ec"
 layout=json.loads((ROOT/"firmware/extracted/xt2-4.41/layout.json").read_text())
 bss=[]
 for s in layout["sections"]:
  for name,(lo,hi) in SPANS.items():
   if overlap(lo,hi,s["bss_base"],s["bss_base"]+s["bss_size"]):bss.append((name,s["id"]))
 assert not bss
 # Native CE50A0 uses 35 selected resource records and three group records.
 # Counts are 64 KiB blocks at CE5154/CE510C, not bytes or initialized sizes.
 tables=[]
 for base,count,stride in [(0xf7ee2c,35,12),(0xf7f054,3,16)]:
  for i in range(count):
   words=struct.unpack("<3I",f.read(base+i*stride,12));flash,n,dest=words
   assert n and dest
   hits=[name for name,(lo,hi) in SPANS.items() if overlap(lo,hi,dest,dest+n*0x10000)]
   enabled = stride==12 or f.word(base+i*stride+12)!=0
   assert not (hits and enabled),(hex(base+i*stride),hits)
   tables.append(dict(record=hex(base+i*stride),destination=hex(dest),end=hex(dest+n*0x10000),blocks=n,enabled=enabled,overlaps=hits))
 # Font resources are a separate table used by the existing font probe.
 fonts=[]
 for i in range(7):
  _,n,dest=struct.unpack("<3I",f.read(0xf7efdc+i*12,12))
  assert dest==0x790000
  assert not any(overlap(lo,hi,dest,dest+n*0x10000) for lo,hi in SPANS.values())
  fonts.append(dict(index=i,blocks=n,destination=hex(dest)))
 initial=f.word(0xfae334);limit=0x13d32fc
 assert initial==0x12532fc
 assert all(not overlap(lo,hi,initial,limit) for lo,hi in SPANS.values())
 # Both literal words and adjacent MOVW/MOVT address construction. This scan is
 # explicitly not a proof that no computed destination can reach the carriers.
 refs={name:[] for name in SPANS};pairs={name:[] for name in SPANS}
 for base,data in f.units:
  words=struct.unpack("<%dI"%(len(data)//4),data[:len(data)//4*4])
  for i,w in enumerate(words):
   for name,(lo,hi) in SPANS.items():
    if lo<=w<hi:refs[name].append(hex(base+i*4))
   if w&0x0ff00000!=0x03000000:continue
   r=(w>>12)&15;low=((w>>4)&0xf000)|(w&4095)
   if i+1==len(words):continue
   z=words[i+1]
   if z&0x0ff00000!=0x03400000 or (z>>12)&15!=r:continue
   value=low|((((z>>4)&0xf000)|(z&4095))<<16)
   for name,(lo,hi) in SPANS.items():
    if lo<=value<hi:pairs[name].append(dict(pc=hex(base+i*4),value=hex(value)))
 assert not refs["code"] and not pairs["code"]
 execution=[]
 if "--execute" in __import__("sys").argv:
  from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
  from unicorn import arm_const as r
  u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(image)+4095)&~4095);u.mem_write(0,image)
  u.mem_map(0x8000000,0x10000)
  transfers=[];writes=[]
  def stop(uc,pc,size,data):
   transfers.append([uc.reg_read(x) for x in (r.UC_ARM_REG_R0,r.UC_ARM_REG_R1,r.UC_ARM_REG_R2,r.UC_ARM_REG_R3)])
   uc.emu_stop()
  def write(uc,access,address,size,value,data):
   assert not any(overlap(lo,hi,address,address+size) for lo,hi in SPANS.values())
   writes.append(address)
  u.hook_add(UC_HOOK_CODE,stop,begin=0xce3c7c,end=0xce3c7c)
  u.hook_add(UC_HOOK_MEM_WRITE,write)
  for index in range(35):
   transfers.clear();u.mem_write(0xfadc60,bytes([255]))
   u.reg_write(r.UC_ARM_REG_R0,index);u.reg_write(r.UC_ARM_REG_SP,0x800e000);u.reg_write(r.UC_ARM_REG_LR,0x800f000)
   u.emu_start(0xce50a0,0x800f000,count=1000)
   assert u.reg_read(r.UC_ARM_REG_PC)==0xce3c7c and len(transfers)==1
   _,n,dest=struct.unpack("<3I",f.read(0xf7ee2c+index*12,12))
   assert transfers[0][1:]==[n,dest,0]
   execution.append(dict(index=index,transfer_arguments=transfers[0],stop_before_transfer=True))
 evidence={}
 for a,b in [(0xce50a0,0xce51b8),(0xcf45a8,0xcf45fc),(0xcf7b24,0xcf7b98)]:
  evidence[hex(a)]=dict(end=hex(b),sha256=hashlib.sha256(f.read(a,b-a)).hexdigest())
 report=dict(scope=__doc__,image_sha256=hashlib.sha256(image).hexdigest(),bss_overlaps=bss,
  resource_reload_records=tables,font_reload_records=fonts,
  newlib_heap=dict(initial=hex(initial),upper_bound=hex(limit),overlap=False,
   limit="Ordinary non-wrapping native sbrk increments; this does not audit every allocator or corrupted state"),
  literal_word_candidates=refs,adjacent_movw_movt_candidates=pairs,
  known_overwrite_routes=[dict(carrier="data",route="CE5168 section2 cold flash reload",effect="Overwrites full 0x6f0000..0x790000 including patch",mitigation="Existing packaged preloaded helper skips transfer; original ROM residency still external"),
   dict(carrier="code",route="Cold section5 decompression",effect="Restores original zero tail",mitigation="Existing preloaded branch; not guaranteed across a real boot")],
  conclusion="No enabled reload-table conflict in CE50A0, BSS or ordinary newlib heap; three disabled group records overlap data and must not be described as disjoint. Global late lifetime remains unproved; permissions do not establish ownership.",
  remaining=["Other allocator registries, computed destinations and indirect consumers remain to be audited", "Continuous later startup and capture CPU/DMA write provenance", "Original SD/ROM load and preloaded flag retention"],
  native_loader_entries=execution,native_function_hashes=evidence,full_boot=False,hardware_verified=False)
 out=ROOT/"research/minimal-lifetime-audit-public-port.json";out.write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(dict(report=str(out),resource_records=len(tables),fonts=len(fonts),literal_candidates={k:len(v) for k,v in refs.items()},conclusion=report["conclusion"])))
if __name__=="__main__":main()
