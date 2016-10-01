from abc import abstractmethod,ABCMeta



class AbstractStatistics(object):
    """
    Abstract class that every Statistics must inherit
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        raise NotImplementedError("Should implement update()")

    @abstractmethod
    def get_results(self):
        raise NotImplementedError("Should implement get_results()")

    @abstractmethod
    def plot_results(self):
        raise NotImplementedError("Should implement plot_results()")

    @abstractmethod
    def load(self):
        raise NotImplementedError("Should implement load()")

    @abstractmethod
    def save(self):
        raise NotImplementedError("Should implement save()")