import time
from functools import wraps

execution_times = {}

def timeit(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter() 
        result = func(*args, **kwargs)
        end = time.perf_counter()
        
        elapsed = end - start
        name = func.__qualname__ 
        
        if name not in execution_times:
            execution_times[name] = {"count": 0, "total_time": 0.0}
            
        execution_times[name]["count"] += 1
        execution_times[name]["total_time"] += elapsed
        return result
    return wrapper

def print_time_stats( fout_log ):

    print("\n=== Summary of executed time ===\n"
         f"{'Function Name':<25} | {'Count':<8} | {'Total Time(s)':<15} | {'Avg Time(s)':<15}",
          file=fout_log
          )
    print( "-" * 70, file=fout_log )
    
    sorted_stats = sorted(execution_times.items(), key=lambda x: x[1]['total_time'], reverse=True)
    for name, stats in sorted_stats:
        avg = stats['total_time'] / stats['count']
        print(f"{name:<25} | {stats['count']:<8} | {stats['total_time']:<15.4f} | {avg:<15.6f}",
          file=fout_log 
                )
