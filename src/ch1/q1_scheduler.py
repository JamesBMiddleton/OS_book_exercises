""" Demonstration of time slicing - you have two tasks which have their own
ram, but must share CPU time - the values (32 bit unsigned ints) in registers 
of the CPU in which operations can be performed (ADD, SUB, MUL) must be swapped
everytime you switch between the two tasks.
This is a 'round robin' scheduler; each task gets the same amount of time
with the registers, and a timer interrupts at regular intervals to swap the
task using this 'time_slice()' function.
"""

registers = [0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,0]
MSP = 13 # kernel stack pointer - 13th register
PC = 15 # program counter - 15th register

pid = [1] # program id
kernelStack = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
tcb1 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # task control block 1
tcb2 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # task control block 2
task1RAM = [0] # task 1's ram
task2RAM = [0] # task 2's ram
systemState = pid + kernelStack + tcb1 + tcb2 + task1RAM + task2RAM

PID = 0 # program id is first element in systemState
PID_END = 1 # there's only two tasks, so last program id is 1
TASK1RAM = 50 # index of task1RAM
TASK2RAM = 51 # index of task2RAM
TCB_OFFSET = 17 # tcb1 starts at index 17 in systemState
TCB_SZ = 16 # tcbs contain 16 elements each

def time_slice(systemState, registers):
    # move CPU register values for current task into kernel stack
    for r in range(0,16):
        systemState[registers[MSP]] = registers[r]
        registers[MSP] += 1

    # get the ID of the TCB for the current task and the one we're switching to 
    pid = systemState[PID]
    if pid == PID_END:
        new_pid = 0
    else:
        new_pid = pid + 1
    systemState[PID] = new_pid

    # TCB for a task is how far from start of the systemState array the TCBs 
    # are, plus the number of TCBs that come before it
    tcb1 = TCB_OFFSET+pid*TCB_SZ
    tcb2 = TCB_OFFSET+new_pid*TCB_SZ
    
    # put the register values for the current task into its TCB storage
    for r in range(0, 16):
        r0 = systemState[registers[MSP]]
        systemState[tcb1+r] = r0
        registers[MSP] -= 1

    # take the register values for next task from TCB, put into kernel stack
    for r in range(0, 16):
        r0 = systemState[tcb2+r]
        systemState[registers[MSP]] = r0
        registers[MSP] += 1

    # take the register values for next task from kernel stack, put into CPU registers
    for r in range(0, 16):
        registers[r] = systemState[registers[MSP]]
        registers[MSP]-=1

    return systemState, registers

def add_five(systemState, registers):
    r0 = systemState[TASK1RAM]
    r1 = 5
    r2 = r0 + r1
    systemState[TASK1RAM] = r2
    return systemState, registers


def add_two(systemState, registers):
    r0 = systemState[TASK2RAM]
    r1 = 2
    r2 = r0 + r1
    systemState[TASK2RAM] = r2
    return systemState, registers


""" So the context here is that you have two programs running which are just
adding 2 or 5 to a total, the total is stored in each program's dedicated RAM.

These tasks require three CPU registers - the current total is put in r0, the
number to add (5 or 2) is put in r1 and the new total is put in r2, which is
then copied to RAM.

The important element missing here is that in an actual CPU, each step in the 
task (assign r0, add r1 and r0...) is controlled by the PC (program counter), 
a special register, rather than just happening automatically because its a 
Python function.

So you're adding five to a total over and over, the CPU receives an interrupt
request from the timer saying 'its time to switch tasks'. You're currently
half way through the 'add_five()' task. You store the current register values 
in RAM (first in kernel stack, then a special spot for storing task registers 
called TCB). You then find the register values for 'add_two()' in its TCB in 
RAM, and put them in the CPU registers. 'add_two()' was halfway through its 
operations when it was interrupted, but the PC register indicates what step 
is next in the task, and all the registers (r0, r1, r2) are exactly what they 
were when the task was interrupted, so it can continue as before.

Note that interrupts can happen mid-task because for every atomic instruction 
(add, mul...) performed by the CPU, it first checks whether it has received any
interrupt requests.

You could simulate this by making the add_two()/add_five() functions check
after every atomic operation whether an interrupt for swapping tasks has been
sent... and then implement interrupts... but then you're starting to build an 
entire basic OS...

Note the register values go CPU->kernel stack->TCB, rather than directly
CPU->TCB. This is to do with separation between kernel and user space.
"""


