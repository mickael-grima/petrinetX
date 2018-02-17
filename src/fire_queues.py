
class FireQueue(list):
    def __init__(self, seq=()):
        super(FireQueue, self).__init__(seq)

    def insert_transition(self, transition, index=-1):
        if transition not in self:
            self.insert(index, transition)

    def is_empty(self):
        return len(self) == 0

    def next(self):
        try:
            return self.pop(0)
        except IndexError as e:
            raise StopIteration(e)

    def optimize(self):
        raise NotImplementedError()


class DefaultFireQueue(FireQueue):
    def optimize(self):
        """
        No ranking algorithm, just keep the transitions that are fire-able
        """
        index = 0
        while index < len(self):
            transition = self[index]
            if not transition.is_fireable():
                del self[index]
            else:
                index += 1
