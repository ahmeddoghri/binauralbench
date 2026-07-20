import json, math, wave, struct
from pathlib import Path

RATE=8000
def ild(left,right):
    l=sum(x*x for x in left); r=sum(x*x for x in right)
    return 10*math.log10(l/r)
def write(path,left,right):
    path.parent.mkdir(exist_ok=True)
    with wave.open(str(path),"w") as w:
        w.setparams((2,2,RATE,0,"NONE","not compressed"))
        frames=[]
        for l,r in zip(left,right):
            frames.append(struct.pack("<hh",int(l*14000),int(r*14000)))
        w.writeframes(b"".join(frames))
def run():
    mono=[math.sin(2*math.pi*330*t/RATE) for t in range(RATE)]
    left=[.9*x for x in mono]; right=[.35*x for x in mono]
    target=ild(left,right)
    collapsed=[.625*x for x in mono]
    naive=ild(collapsed,collapsed)
    linked_l=[.86*x for x in mono]; linked_r=[.34*x for x in mono]
    linked=ild(linked_l,linked_r)
    write(Path("demo/input_binaural.wav"),left,right); write(Path("demo/preserved.wav"),linked_l,linked_r)
    e1=abs(naive-target); e2=abs(linked-target)
    return {"target_ild_db":round(target,2),"naive_ild_db":round(naive,2),
            "linked_ild_db":round(linked,2),"ild_error_reduction_pct":round(100*(1-e2/e1),1)}
if __name__=="__main__": print(json.dumps(run(),indent=2))
