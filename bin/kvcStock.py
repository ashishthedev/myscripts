def main():

    r1715 = 1.146 / 24 * 4400
    r2218 = 2.220 / 24 * 4400
    finalAmount = 58997
    fmt = "{:<20}{:<20}{:<20}"
    print(fmt.format("17x15", "22x18", "diff"))
    for q1715 in range(1000):
        for q2218 in range(1000):
            amt = q1715 * r1715 + q2218*r2218
            diff = abs(amt - finalAmount)
            if diff<5:
                print(fmt.format(q1715, q2218, diff))


if __name__ == '__main__':
    main()
