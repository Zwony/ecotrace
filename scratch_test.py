from ecotrace import EcoTrace
eco = EcoTrace(quiet=True)

@eco.track
def my_test_function():
    return sum(i * i for i in range(1000000))

if __name__ == "__main__":
    my_test_function()
