#########################################################
##
## Date: 14-June-2012
## Author: Ashish Anand
## Intent: To provide a momoization decrator that can be
##         applied to any class or function
#########################################################

from Util.Misc import PrintInBox

from functools import wraps

def _getIDTuple(fn, args, kwargs):
    """Some quick and dirty way to generate a unique key for a specific call"""
    l=[fn.func_name]  # For faster performance we are using function name instead of its id. Might break if polymorphism comes into picture
    for arg in args:
        l.append(str(arg))
    if kwargs:
        for k, v in kwargs.items():
            l.append(k)
            l.append(id(v))
    return tuple(l)

_memoized = dict()


def memoize(f):
    """ A basic memoizer decorator """
    @wraps(f)
    def memoize_wrapper_around_original_function(*args, **kwargs):
        key = _getIDTuple(f, args, kwargs)
        if key not in _memoized:
            _memoized[key]=f(*args, **kwargs)
        #TODO: Find out the size of _memoized with print function and see if we are abusing it
        return _memoized[key]
    return memoize_wrapper_around_original_function

def timeThisFunction(f):
    """ A basic timer decorator """
    @wraps(f)
    def timed_decorated_function(*args, **kwargs):
        import time
        t = time.clock()
        retVal = f(*args, **kwargs)  # Call the function.
        print("Time taken for {} is: {} seconds".format(f.func_name, time.clock() - t))  # And Print time taken by this function
        return retVal
    return timed_decorated_function


def RetryNTimes(noOfTimes):
  def RetryDecoratorGenerator(f):
    @wraps(f)
    def Retry_decorated_function(*args, **kwargs):
      missionAccomplished = False
      attempts = 0
      while not missionAccomplished and (attempts < noOfTimes):
        try:
          attempts += 1
          retVal = f(*args, **kwargs)
          missionAccomplished = True  # If no exception thrown, it means it went through.
          return retVal
        except Exception as ex:
          PrintInBox(str(ex))
          if attempts < noOfTimes:
            print("Retrying one more time...")
          else:
            PrintInBox("Bailing out. Enough for today...")
            raise ex
    return Retry_decorated_function
  return RetryDecoratorGenerator
