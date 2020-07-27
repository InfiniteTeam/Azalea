class AzaleaData:
    def __repr__(self):
        reprs = []
        for key, value in zip(self.__dict__.keys(), self.__dict__.values()):
            reprs.append(f'{key}={value.__repr__()}')
        reprstr = f'<{self.__class__.__name__}: ' + ' '.join(reprs) + '>'
        return reprstr

class AzaleaManager:
    pass

class AzaleaDBManager:
    pass