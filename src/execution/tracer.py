import sys
import trace
import threading

from .results import Results

class Tracer(trace.Trace):
    def __init__(self, count=1, trace=0, countfuncs=0, countcallers=0,
                        ignoremods=(), ignoredirs=[sys.prefix, sys.exec_prefix], infile=None, outfile=None,
                        timing=False):
        super().__init__(count, trace, countfuncs, countcallers,
                        ignoremods, ignoredirs, infile, outfile,
                        timing)
        
    def variable_trace(self, var_dict:dict):
        for k, v in var_dict.items():
            if k not in Results.vari_names:
                continue
            v = str(v)
            if k not in Results.vari_traces.keys():
                Results.vari_traces[k] = []
            if len(Results.vari_traces[k]) == 0 or \
                    Results.vari_traces[k][-1] != v:
                Results.vari_traces[k].append(v)
    
    def execution_trace(self, lineno:int):
        Results.exec_traces.append(lineno)
    
    def localtrace_count(self, frame, why, arg):
        if why == "line":
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            key = filename, lineno
            self.counts[key] = self.counts.get(key, 0) + 1
            # append line numbers to traces list
            self.execution_trace(lineno)
        # append variable values
        self.variable_trace(frame.f_locals)
        return self.localtrace
    
    def runctx(self, cmd, globals=None, locals=None):
        # runctx 함수 절대 삭제 금지!
        if globals is None: globals = {}
        if locals is None: locals = {}
        if not self.donothing:
            threading.settrace(self.globaltrace)
            sys.settrace(self.globaltrace)
        try:
            exec(cmd)
        finally:
            if not self.donothing:
                sys.settrace(None)
                threading.settrace(None)