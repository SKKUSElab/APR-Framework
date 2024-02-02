import random


class Randoms:
    seed = 0

    @classmethod
    def choice(cls, elements):
        random.seed(cls.seed)
        return random.choice(elements)
    
    @classmethod
    def sample(cls, elements, size):
        random.seed(cls.seed)
        return random.sample(elements, size)

    @classmethod
    def shuffle(cls, elements):
        random.seed(cls.seed)
        return random.shuffle(elements)
    
    @classmethod
    def uniform(cls, start, end):
        return random.uniform(start, end)