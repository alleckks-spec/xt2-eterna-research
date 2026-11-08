"""Check that the alias inventory finds deliberately writable alternate maps.
Synthetic descriptor tables only, with no Unicorn or vendor input dependency.
"""
import struct
from xt2_carrier_alias_inventory import inventory
class Memory:
 def __init__(self):self.words={}
 def put(self,a,v):self.words[a]=v
 def mem_read(self,a,n):
  assert n==4
  return struct.pack('<I',self.words.get(a,0))
def main():
 m=Memory();table=0x10000
 # Native-like small pages for the three data pages and the code tail page.
 for va,physical in [(0x700000,0x700000),(0xd00000,0xd00000)]:
  l2=0x20000+(va>>20)*1024;m.put(table+(va>>20)*4,l2|1)
  for i in range(256):m.put(l2+4*i,(physical+i*4096)|0x232)
 base=inventory(m,table)
 assert [r['address'] for r in base['aliases']['data']]==[0x781000,0x782000,0x783000]
 assert [r['address'] for r in base['aliases']['code']]==[0xdf7000]
 # A writable section alias must be reported even when the original is RO.
 m.put(table+(0x40700000>>20)*4,0x700000|(3<<10)|2)
 aliases=inventory(m,table)['aliases']['data']
 assert len(aliases)==6
 assert {r['address'] for r in aliases if r['ap']==3}=={0x40781000,0x40782000,0x40783000}
 # Repeated large-page descriptors must yield each virtual 4K page exactly once.
 l2=0x40000;m.put(table+(0x50700000>>20)*4,l2|1)
 for i in range(0x80,0x90):m.put(l2+4*i,0x780000|(3<<4)|1)
 rows=inventory(m,table)['aliases']['data'];assert len(rows)==9
 assert {r['address'] for r in rows if r['kind']=='large_page'}=={0x50781000,0x50782000,0x50783000}
 # A supersection repeats16 L1 descriptors; preserve the virtual MiB offset.
 for i in range(16):m.put(table+((0x60000000>>20)+i)*4,(1<<18)|(3<<10)|2)
 final=inventory(m,table)
 assert len(final['aliases']['data'])==12
 assert {r['address'] for r in final['aliases']['data'] if r['kind']=='supersection'}=={0x60781000,0x60782000,0x60783000}
 assert {r['address'] for r in final['aliases']['code'] if r['kind']=='supersection'}=={0x60df7000}
 print('PASS: identity, writable section, large-page and supersection aliases')
if __name__=='__main__':main()
