from sender import *
setup(port = "5556")

while True:
    a = input()
    if a!="ter":
        execute(a)
    else:
        terminate()
