# This is an improved version of python's heapq.
# It keeps track of item locations so that it can support decrease() in log time,
# which is required for a fast Dijkstra's algorithm
class Heap:
    def __init__(self):
        self.a = []
        self.ind_dict = {}

    def siftdown(self, startpos, pos):
        heap = self.a
        newitem = heap[pos]
        # Follow the path to the root, moving parents down until finding a place
        # newitem fits.
        while pos > startpos:
            parentpos = (pos - 1) >> 1
            parent = heap[parentpos]
            if newitem < parent:
                heap[pos] = parent
                self.ind_dict[parent] = pos
                pos = parentpos
                continue
            break
        heap[pos] = newitem
        self.ind_dict[newitem] = pos
        return pos

    def siftup(self, pos):
        heap = self.a
        endpos = len(heap)
        startpos = pos
        newitem = heap[pos]
        # Bubble up the smaller child until hitting a leaf.
        childpos = 2*pos + 1    # leftmost child position
        while childpos < endpos:
            # Set childpos to index of smaller child.
            rightpos = childpos + 1
            if rightpos < endpos and not heap[childpos] < heap[rightpos]:
                childpos = rightpos
            # Move the smaller child up.
            heap[pos] = heap[childpos]
            self.ind_dict[heap[childpos]] = pos
            pos = childpos
            childpos = 2*pos + 1
        # The leaf at pos is empty now.  Put newitem there, and bubble it up
        # to its final resting place (by sifting its parents down).
        heap[pos] = newitem
        self.ind_dict[newitem] = pos
        self.siftdown(startpos, pos)

    def push(self, item):
        """Push item onto heap, maintaining the heap invariant."""
        heap = self.a
        heap.append(item)
        return self.siftdown(0, len(heap)-1)

    def pop(self):
        """Pop the smallest item off the heap, maintaining the heap invariant."""
        heap = self.a
        last = heap.pop()    # raises appropriate IndexError if heap is empty

        if heap:
            returnitem = heap[0]
            heap[0] = last
            self.ind_dict[last] = 0
            self.siftup(0)
        else:
            returnitem = last
        return returnitem

    def decrease(self, x, new_x):
        heap = self.a
        ind = self.ind_dict[x]
        heap[ind] = new_x
        self.siftdown(0, ind)

if __name__ == '__main__':
    h = Heap()
    [h.push(i) for i in [4,6,7,2,3,8]]
