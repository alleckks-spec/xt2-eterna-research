"""Read ARM short-descriptor mappings, including large pages/supersections."""
import struct


def inspect(uc,address,table):
    word=lambda a:struct.unpack('<I',uc.mem_read(a,4))[0]
    first=word(table+(address>>20)*4)
    row=dict(address=address,l1=first)
    if first&3==2:
        supersection=bool(first&(1<<18))
        mask=0xff000000 if supersection else 0xfff00000
        row.update(kind='supersection' if supersection else 'section',
            physical=(first&mask)|(address&(~mask&0xffffffff)),
            ap=((first>>10)&3)|((first>>13)&4),xn=bool(first&16))
    elif first&3==1:
        second=word((first&~1023)+((address>>12)&255)*4)
        row['l2']=second
        if second&3==0:raise ValueError(f'Unmapped L2 for {address:#x}')
        large=second&3==1
        mask=0xffff0000 if large else 0xfffff000
        row.update(kind='large_page' if large else 'small_page',
            physical=(second&mask)|(address&(~mask&0xffffffff)),
            ap=((second>>4)&3)|((second>>7)&4),xn=bool(second&(0x8000 if large else 1)))
    else:raise ValueError(f'Unmapped/unsupported L1 for {address:#x}')
    return row
