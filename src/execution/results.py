class Results:
    exec_traces = []
    vari_traces = {}
    vari_names = []
    status = None
    timeout = 1
    test_code = ''
    input_tc = ''
    output_tc = ''
    output = None
    globals = None

    @classmethod
    def init_global_vars(cls):
        cls.exec_traces = []
        cls.vari_traces = {}
        cls.vari_names = []
        cls.status = None
        cls.timeout = 1
        cls.test_code = ''
        cls.input_tc = ''
        cls.output_tc = ''
        cls.output = None
        cls.globals = None