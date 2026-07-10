import sys
import json
import os
import time
import pickle
import math
import threading
import queue
import atexit

sys.set_int_max_str_digits(0)

OUTPUT = "output.txt"
STATE = "state.pkl"

C = 640320
C3_OVER_24 = C ** 3 // 24

BLOCK_SIZE = 400
CHECKPOINT_EVERY = 500

save_queue = queue.Queue()
save_thread = None
stop_save_thread = threading.Event()

try:
    import gmpy2
    USE_GMPY2 = True
    mpz = gmpy2.mpz
    def isqrt(n):
        return int(gmpy2.isqrt(n))
except ImportError:
    USE_GMPY2 = False
    mpz = int
    def isqrt(n):
        return math.isqrt(n)

C3_OVER_24 = mpz(C3_OVER_24)
CONST_13591409 = mpz(13591409)
CONST_545140134 = mpz(545140134)
CONST_426880 = mpz(426880)
CONST_10005 = mpz(10005)

def save_worker():
    while not stop_save_thread.is_set():
        try:
            state = save_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if state is None:
            break
        temp = STATE + ".tmp"
        try:
            with open(temp, "wb") as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(temp, STATE)
        except Exception:
            try:
                os.remove(temp)
            except OSError:
                pass
        finally:
            save_queue.task_done()

def start_save_thread():
    global save_thread
    if save_thread is None or not save_thread.is_alive():
        save_thread = threading.Thread(target=save_worker, daemon=False)
        save_thread.start()

def stop_save_thread_and_discard():
    global save_thread
    if save_thread is not None and save_thread.is_alive():
        stop_save_thread.set()
        while not save_queue.empty():
            try:
                save_queue.get_nowait()
                save_queue.task_done()
            except queue.Empty:
                break
        save_queue.put(None)
        save_thread.join(timeout=3)
        save_thread = None
        stop_save_thread.clear()

def async_save_state(state):
    save_queue.put(state)

def save_state_sync(state):
    temp = STATE + ".tmp"
    try:
        with open(temp, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(temp, STATE)
    except Exception as e:
        print(f"Warning: Failed to save state: {e}")
        try:
            os.remove(temp)
        except OSError:
            pass

def load_state():
    if not os.path.exists(STATE):
        return None
    with open(STATE, "rb") as f:
        return pickle.load(f)

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
    names = ["current", "index", "P", "Q", "T"]
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
    p = done / total if total else 0
    width = 40
    bar = int(width * p)
    speed = done / (time.time() - start) if done else 0
    print(
        f"\r[{'#' * bar}{'-' * (width - bar)}] "
        f"{p * 100:.2f}% {done}/{total} "
        f"{speed:.2f} it/s",
        end="",
        flush=True
    )

def bs(a, b):
    if b - a == 1:
        if a == 0:
            return mpz(1), mpz(1), CONST_13591409
        P = mpz((6 * a - 5) * (2 * a - 1) * (6 * a - 1))
        Q = mpz(a * a * a) * C3_OVER_24
        T = P * (CONST_13591409 + CONST_545140134 * mpz(a))
        if a & 1:
            T = -T
        return P, Q, T
    m = (a + b) // 2
    P1, Q1, T1 = bs(a, m)
    P2, Q2, T2 = bs(m, b)
    return (P1 * P2, Q1 * Q2, T1 * Q2 + P1 * T2)

def calculate(add_digits, block_size):
    old = load_state()
    if old:
        current, index, P, Q, T = old
    else:
        current, index, P, Q, T = 0, 0, mpz(1), mpz(1), mpz(0)

    target = current + add_digits
    old_terms = current // 14 + 1
    new_terms = target // 14 + 1

    print(f"current {current} digits")
    print(f"add {add_digits} digits")
    print(f"block size: {block_size}")
    start = time.time()

    try:
        blocks_done = 0
        while index < new_terms:
            end = min(index + block_size, new_terms)
            p, q, t = bs(index, end)
            if index == 0:
                P, Q, T = p, q, t
            else:
                T = T * q + P * t
                P = P * p
                Q = Q * q
            index = end
            blocks_done += 1

            if blocks_done % max(1, 10000 // block_size) == 0 or index >= new_terms:
                async_save_state((target, index, P, Q, T))

            progress(index - old_terms, new_terms - old_terms, start)

    except KeyboardInterrupt:
        stop_save_thread_and_discard()
        save_state_sync((target, index, P, Q, T))
        print("\nsaved (interrupt)")
        return None

    stop_save_thread_and_discard()
    save_state_sync((target, index, P, Q, T))

    print("\ncomputing final pi value...")
    scale = target + 10
    sqrt_val = isqrt(CONST_10005 * (mpz(10) ** (2 * scale)))
    pi = (CONST_426880 * sqrt_val * Q) // T
    s = str(pi)
    result = s[:-scale] + "." + s[-scale:][:target]
    return result

def main():
    global BLOCK_SIZE, CHECKPOINT_EVERY

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

    add_digits = None
    block_size = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--block-size="):
            try:
                block_size = int(arg.split("=")[1])
            except ValueError:
                print("invalid block size")
                return
        elif arg.startswith("--"):
            try:
                add_digits = int(arg[2:])
            except ValueError:
                print("invalid digit count")
                return
        i += 1

    if add_digits is None:
        print("usage: python m.py --1000 [--block-size=N]")
        return

    if block_size is not None:
        BLOCK_SIZE = max(1, block_size)
    CHECKPOINT_EVERY = max(1, 10000 // BLOCK_SIZE)

    start_save_thread()
    atexit.register(stop_save_thread_and_discard)

    t = time.time()
    result = calculate(add_digits, BLOCK_SIZE)
    if result:
        with open(OUTPUT, "w") as f:
            f.write(result)
        print("done", round(time.time() - t, 2), "s")
        print("saved output.txt")

if __name__ == "__main__":
    main()
