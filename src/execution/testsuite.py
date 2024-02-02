class TestSuite:
    def __init__(self, testcases):
        self.testcases = testcases
        self.current_index = 0

    def __iter__(self):
        self.current_index = 0
        return self

    def __next__(self):
        if self.current_index < len(self.testcases):
            testcase = self.testcases[self.current_index]
            self.current_index += 1
            return testcase
        raise StopIteration
    
    def __len__(self):
        return len(self.testcases)
    
    def __str__(self):
        prints = ''
        for testcase in self.testcases:
            prints += f"Testcase No: {testcase['testcase_no']}\n"
            prints += f"Input: {testcase['input_tc']}\n"
            prints += f"Output: {testcase['output_tc']}\n"
        return prints
    
    def print_testcase(self, idx):
        prints = ''
        for testcase in self.testcases:
            if testcase['testcase_no'] == idx:
                prints += f"Testcase No: {testcase['testcase_no']}\n"
                prints += f"Input: {testcase['input_tc']}\n"
                prints += f"Output: {testcase['output_tc']}"
        return prints

    def get_open_tc_list(self):
        return [tc for tc in self.testcases if tc['is_open']]

    def get_tc_no_list(self):
        return [tc['testcase_no'] for tc in self.testcases]
    
    def get_tc_by_no(self, testcase_no):
        for testcase in self.testcases:
            if testcase['testcase_no'] == testcase_no:
                return testcase
        raise IndexError