
class FireQueue(object):
    def __init__(self):
        self.queue = []

    def insert_transition(self, transition, index=-1):
        self.queue.insert(index, transition)

    def is_empty(self):
        return len(self.queue) == 0

    def next(self):
        try:
            return self.queue.pop(0)
        except IndexError as e:
            return StopIteration(e)

    def optimize(self):
        raise NotImplementedError()


class DefaultFireQueue(FireQueue):
    def optimize(self):
        """
        No ranking algorithm, just keep the transitions that are fire-able
        """
        index = 0
        while index < len(self.queue):
            transition = self.queue[index]
            if not transition.is_fireable():
                del self.queue[index]
            else:
                index += 1
