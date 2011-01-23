from threading import Thread, Lock, Semaphore

class AsyncQueue (Thread):
    def __init__ (self):
        self.queue= []
        self.lock= Lock ()
        self.count= 0
        self.sem= Semaphore (0)
        self.finish= False
        Thread.__init__ (self)

    def append (self, *args):
        self.lock.acquire ()
        print "AQ.append(): lock!..."
        self.queue.append (args)
        print "AQ.append(): ... and loaded!"
        self.count+= 1
        self.sem.release ()
        self.lock.release ()

    def insert (self, *args):
        self.lock.acquire ()
        print "AQ.insert(): lock!..."
        self.queue.insert (0, args)
        print "AQ.insert(): ... and loaded!"
        self.count+= 1
        self.sem.release ()
        self.lock.release ()

    def run (self):
        # for obj, methodName, args, kwargs, signalName in self.queue
        print "AQ.run(): start!"
        while not self.finish:
            self.sem.acquire () # this might block
            if self.count>0:
                self.count-= 1
                print "AQ.run(): something in the q, %d left" % self.count
                self.lock.acquire ()
                obj, methodName, args, kwargs, signalName= self.queue.pop (0)
                self.lock.release ()
                try:
                    method= getattr (obj, methodName)
                    print "AQ.run(): got method"
                    # signal= getattr (obj, signalName)
                    # print "AQ.run(): got signal"
                except AttributeError:
                    print "foo"
                else:
                    try:
                        print "AQ.run(): method()"
                        value= method (*args, **kwargs)
                        # signal.emit (value)
                        # print "AQ.run(): signal emited!"
                    except Exception, e:
                        print "bar: %s" % e
            else:
                print "AQ.run(): nothing in the q"
                # self.finish= True

        print "AQ.run(): finished!"

    def stop (self):
        self.finish= True
        self.sem.release ()

# end
