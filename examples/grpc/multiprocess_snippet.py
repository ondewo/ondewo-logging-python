from multiprocessing import Process, current_process

from ondewo.logging.logger import logger_console


def worker():
    logger_console.info({"message": f"hello from {current_process().pid}"})


if __name__ == "__main__":
    procs = [Process(target=worker) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print("all done")
