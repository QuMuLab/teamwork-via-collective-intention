
import os, sys, time


from parser import parse

def cleanup():
    os.system('rm -f domain.pddl')
    os.system('rm -f problem.pddl')
    #os.system('rm -f output.txt')
    #os.system('rm -f output.txt.err')
    os.system('rm -f human_policy.out')
    os.system('rm -f policy.out')
    os.system('rm -f graph.dot')
    os.system('rm -f action.map')
    os.system('rm -f unhandled.states')
    os.system('./cleanup')

def solve(fname):

    print

    t_start = time.time()

    print "Parsing problem...",
    sys.stdout.flush()
    problem = parse(fname)
    print "done!"

    print "Compiling problem..."
    sys.stdout.flush()
    problem.compile()
    print "done!"

    print "\nSolving problem...",
    sys.stdout.flush()
    problem.solve()
    print "done!"

    print "\nTime: %f s" % (time.time() - t_start)

    print
    problem.output_solution()

    print


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "\nUsage: python planner.py <teamwork problem file> [--keep-files]\n"
        sys.exit(1)

    solve(sys.argv[1])

    if len(sys.argv) < 3 or '--keep-files' != sys.argv[2]:
        cleanup()
