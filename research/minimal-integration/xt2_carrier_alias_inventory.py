"""Enumerate current 32-bit ARM stage-1 aliases for the two fixed carriers.
Original Codex-assisted analysis; no firmware bytes, DMA or future-map claims.
Uses arm_page_policy.inspect and the caller's actual populated L1/L2 tables.
"""
import struct
from arm_page_policy import inspect
SPANS={'data':(0x781000,0x784000),'code':(0xdf7900,0xdf8000)}
def inventory(uc,table):
 aliases={name:[] for name in SPANS};coarse=0;sections=0
 def retain(virtual,physical,extent):
  for name,(lo,hi) in SPANS.items():
   if max(physical,lo)>=min(physical+extent,hi):continue
   first=max(physical,lo)&~4095;last=(min(physical+extent,hi)+4095)&~4095
   for page in range(first,last,4096):
    va=virtual+page-physical
    aliases[name].append(inspect(uc,va,table))
 for index in range(4096):
  va=index<<20;word=struct.unpack('<I',uc.mem_read(table+4*index,4))[0]
  kind=word&3
  if kind==0:continue
  if kind==2:
   # Each L1 slot covers one virtual MiB, including repeated supersections.
   if word&(1<<18) and word&0x00f001e0:raise ValueError('Extended physical supersection unsupported')
   sections+=1;retain(va,inspect(uc,va,table)['physical'],1<<20)
  elif kind==1:
   coarse+=1;l2=word&~1023
   for j in range(256):
    entry=struct.unpack('<I',uc.mem_read(l2+4*j,4))[0]
    if entry&3:retain(va+(j<<12),inspect(uc,va+(j<<12),table)['physical'],4096)
  else:raise ValueError('Reserved L1 descriptor')
 # Same virtual page can appear twice only if the inventory itself is wrong.
 for rows in aliases.values():assert len(rows)==len({r['address'] for r in rows})
 return dict(table=hex(table),l1_slots=4096,section_slots=sections,coarse_slots=coarse,aliases=aliases,
  limits='Current 32-bit stage-1 table only; no future mappings, other masters or hardware DMA alias proof.')
