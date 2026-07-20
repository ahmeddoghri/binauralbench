import json, math, random, wave, struct
from pathlib import Path

RATE=8000

def ild(left,right):
    l=sum(x*x for x in left)+1e-9; r=sum(x*x for x in right)+1e-9
    return 10*math.log10(l/r)

def write(path,left,right):
    path.parent.mkdir(exist_ok=True)
    with wave.open(str(path),"w") as w:
        w.setparams((2,2,RATE,0,"NONE","not compressed"))
        frames=[]
        for l,r in zip(left,right):
            frames.append(struct.pack("<hh",int(l*14000),int(r*14000)))
        w.writeframes(b"".join(frames))

def estimate_gain(mix, ref):
    num = sum(m*r for m,r in zip(mix, ref))
    den = sum(r*r for r in ref) + 1e-9
    return num/den

def run(seed=43):
    rng = random.Random(seed)
    target = [math.sin(2*math.pi*330*t/RATE) for t in range(RATE)]
    interferer = [math.sin(2*math.pi*770*t/RATE + 0.4) for t in range(RATE)]
    gL, gR = .9, .35
    hL, hR = .3, .9
    mix_L = [gL*t + hL*i + rng.gauss(0,.02) for t,i in zip(target, interferer)]
    mix_R = [gR*t + hR*i + rng.gauss(0,.02) for t,i in zip(target, interferer)]

    gL_hat = estimate_gain(mix_L, target)
    gR_hat = estimate_gain(mix_R, target)

    # naive: collapses the two independently-estimated channel gains into one shared
    # gain before rendering both channels, which is what happens when a separator
    # solves each ear independently and then normalizes to a common output level.
    avg_gain = (gL_hat + gR_hat) / 2
    naive_L = [avg_gain * x for x in target]
    naive_R = [avg_gain * x for x in target]

    # linked: keeps each channel's own estimated gain instead of collapsing them.
    linked_L = [gL_hat * x for x in target]
    linked_R = [gR_hat * x for x in target]

    target_ild = ild([gL*x for x in target], [gR*x for x in target])
    naive_ild = ild(naive_L, naive_R)
    linked_ild = ild(linked_L, linked_R)

    write(Path("demo/input_binaural.wav"), mix_L, mix_R)
    write(Path("demo/preserved.wav"), linked_L, linked_R)

    e1 = abs(naive_ild - target_ild)
    e2 = abs(linked_ild - target_ild)
    return {"target_ild_db":round(target_ild,2),"naive_ild_db":round(naive_ild,2),
            "linked_ild_db":round(linked_ild,2),"ild_error_reduction_pct":round(100*(1-e2/e1),1)}

if __name__=="__main__": print(json.dumps(run(),indent=2))
