#########################################################
##
## Date: 14-June-2012
## Author: Ashish Anand
## Intent: To provide a momoization decrator that can be
##         applied to any class or function
#########################################################

from UtilMisc import PrintInBox

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

def memoize(function_to_decorate):
    """ A basic memoizer decorator """
    def memoize_wrapper_around_original_function(*args, **kwargs):
        key = _getIDTuple(function_to_decorate, args, kwargs)
        if key not in _memoized:
            _memoized[key]=function_to_decorate(*args, **kwargs)
        #TODO: Find out the size of _memoized with print function and see if we are abusing it
        return _memoized[key]
    return memoize_wrapper_around_original_function

def timeThisFunction(function_to_decorate):
    """ A basic timer decorator """
    def timeThisFunction_wrapper_around_original_function(*args, **kwargs):
        import time
        t = time.clock()
        retVal = function_to_decorate(*args, **kwargs)  # Call the function.
        print("Time taken for {} is: {} seconds".format(function_to_decorate.func_name, time.clock() - t))  # And Print time taken by this function
        return retVal
    return timeThisFunction_wrapper_around_original_function

def RetryFor5TimesIfFailed(function_to_decorate):
    """A decorator that will call the function 5 times if it fails(i.e. throws exception) and will bail out in the end."""
    def retry_wrapper_around_original_function(*args, **kwargs):
        missionAccomplished = False
        MAX_RETRIES = 5
        attempts = 0
        while not missionAccomplished and (attempts < MAX_RETRIES):
            try:
                attempts += 1
                retVal = function_to_decorate(*args, **kwargs)
                missionAccomplished = True  # If no exception thrown, it means it went through.
                return retVal
            except Exception as ex:
                PrintInBox(str(ex))
                if attempts < MAX_RETRIES:
                    print("Retrying one more time...")
                else:
                    PrintInBox("Bailing out. Enough for today...")
    return retry_wrapper_around_original_function

