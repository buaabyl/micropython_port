import utime

def loop():
    t1 = 0
    t2 = 0
    for i in range(5):
        t1 = utime.ticks_us()
        u = 0
        for j in range(1000):
            u = i + j
            pass
        t2 = utime.ticks_us()
        print('duration', t2 - t1, u)

loop()

