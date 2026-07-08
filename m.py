import sys
sys.set_int_max_str_digits(0)

import json
import os
import time
import pickle
import math


OUTPUT = "output.txt"
STATE = "state.pkl"

C = 640320
C3_OVER_24 = C ** 3 // 24

def verify_state():
    if not os.path.exists(STATE):
        print("state.pkl not found")
        return

    if not os.path.exists("state.json"):
        print("state.json not found")
        return

    with open(STATE, "rb") as f:
        pkl = pickle.load(f)

    with open("state.json") as f:
        data = json.load(f)

    js = (
        data["current"],
        data["index"],
        int(data["P"]),
        int(data["Q"]),
        int(data["T"])
    )

    names = [
        "current",
        "index",
        "P",
        "Q",
        "T"
    ]

    ok = True

    for name, a, b in zip(names, pkl, js):
        if a != b:
            print(name, "differs")
            ok = False

    if ok:
        print("state files match")

def transfer_to_json():
    if not os.path.exists(STATE):
        print("state.pkl not found")
        return

    with open(STATE, "rb") as f:
        current, index, P, Q, T = pickle.load(f)

    data = {
        "current": current,
        "index": index,
        "P": str(P),
        "Q": str(Q),
        "T": str(T)
    }

    with open("state.json", "w") as f:
        json.dump(data, f)

    print("state.json created")


def transfer_to_pkl():
    if not os.path.exists("state.json"):
        print("state.json not found")
        return

    with open("state.json") as f:
        data = json.load(f)

    state = (
        data["current"],
        data["index"],
        int(data["P"]),
        int(data["Q"]),
        int(data["T"])
    )

    with open(STATE, "wb") as f:
        pickle.dump(state, f)

    print("state.pkl created")

def progress(done, total, start):
    p = done / total
    width = 40
    bar = int(width * p)
    speed = done / (time.time() - start)

    print(
        f"\r[{'#' * bar}{'-' * (width-bar)}] "
        f"{p*100:.2f}% {done}/{total} "
        f"{speed:.2f} it/s",
        end="",
        flush=True
    )


def bs(a, b):
    if b - a == 1:
        if a == 0:
            return 1, 1, 13591409

        P = (6*a-5)*(2*a-1)*(6*a-1)
        Q = a*a*a*C3_OVER_24
        T = P * (13591409 + 545140134*a)

        if a & 1:
            T = -T

        return P, Q, T

    m = (a + b) // 2

    P1, Q1, T1 = bs(a, m)
    P2, Q2, T2 = bs(m, b)

    return (
        P1 * P2,
        Q1 * Q2,
        T1 * Q2 + P1 * T2
    )


def save_state(state):
    with open(STATE, "wb") as f:
        pickle.dump(state, f)


def load_state():
    if not os.path.exists(STATE):
        return None

    with open(STATE, "rb") as f:
        return pickle.load(f)


def calculate(add_digits):

    old = load_state()

    if old:
        current, index, P, Q, T = old
    else:
        current, index, P, Q, T = 0, 0, 1, 1, 0

    target = current + add_digits

    old_terms = current // 14 + 1
    new_terms = target // 14 + 1

    block = 20

    print(
        f"current {current} digits"
    )

    print(
        f"add {add_digits} digits"
    )

    start = time.time()

    try:
        while index < new_terms:

            end = min(
                index + block,
                new_terms
            )

            p, q, t = bs(index, end)

            if index == 0:
                P, Q, T = p, q, t
            else:
                T = T*q + P*t
                P = P*p
                Q = Q*q

            index = end

            save_state(
                (
                    target,
                    index,
                    P,
                    Q,
                    T
                )
            )

            progress(
                index-old_terms,
                new_terms-old_terms,
                start
            )

    except KeyboardInterrupt:
        save_state(
            (
                target,
                index,
                P,
                Q,
                T
            )
        )

        print("\nsaved")
        return None

    print()

    scale = target + 20

    sqrt = math.isqrt(
        10005 * 10 ** (2 * scale)
    )

    pi = (
        426880
        * sqrt
        * Q
        //
        T
    )

    s = str(pi)

    result = (
        s[:-scale]
        +
        "."
        +
        s[-scale:][:target]
    )

    return result



def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == "--transfer-to-json":
            transfer_to_json()
            return
    
        if sys.argv[1] == "--transfer-to-pkl":
            transfer_to_pkl()
            return
            
        if sys.argv[1] == "--verify":
            verify_state()
            return

    if len(sys.argv) != 2:
        print(
            "usage: python m.py --1000"
        )
        return

    add_digits = int(
        sys.argv[1][2:]
    )

    t = time.time()

    result = calculate(
        add_digits
    )

    if result:

        with open(
            OUTPUT,
            "w"
        ) as f:
            f.write(result)

        print(
            "done",
            round(time.time()-t,2),
            "s"
        )

        print(
            "saved output.txt"
        )


if __name__ == "__main__":
    main()