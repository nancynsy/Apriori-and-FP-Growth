# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:30:54 2016

@author: nancynan
"""

from collections import defaultdict, namedtuple
import time

class fp:
    def __init__(self, minimum_support):
        self.input_file = 'adult_data.csv'
        self.minimum_support = minimum_support

    def run(self):
        self.results = list(self.find_frequent_itemsets(self.open_file(), True))
        self.results = sorted(self.results, key=lambda x: x[1], reverse=True)

    def printResults(self):
        i = 1
        for itemset, support in self.results:
            print ('Item %d: %s, Support: %.3f' % (i, ', '.join(itemset), float(support) / self.transaction_size))
            i += 1

    def writeResults(self):
        with open('fpgrowth_output.csv', 'w') as f:
            for itemset, support in self.results:
                f.write('%.3f, %s\n' % (float(support) / self.transaction_size, ','.join(itemset)))

    def open_file(self):
        with open(self.input_file, 'rU') as f:
            for line in f:
                lines = line.strip().split(',')
                lines[0] = 'age:'+lines[0]
                lines[1] = 'workclass:'+lines[1]
                lines[2] = 'fnlwgt:'+lines[2]
                lines[3] = 'education:'+lines[3]
                lines[4] = 'ed_num:'+lines[4]
                lines[5] = 'marital-status:'+lines[5]
                lines[6] = 'occupation:'+lines[6]
                lines[7] = 'relationship:'+lines[7]
                lines[8] = 'race:'+lines[8]
                lines[9] = 'sex:'+lines[9]
                lines[10] = 'capital-gain:'+lines[10]
                lines[11] = 'capital-loss:'+lines[11]
                lines[12] = 'hrs-per-week:'+lines[12]
                lines[13] = 'native-country:'+lines[13]
                yield lines

    def find_frequent_itemsets(self,transactions,include_support=False):
        # generate fptree 
        # mine freqpat 
        # (itemset, support) yielded when include_support true

        items = defaultdict(int)  
        all_transactions = []

        for transaction in transactions:
            single_trans = []
            for item in transaction:
                items[item] += 1
                single_trans.append(item)
            all_transactions.append(single_trans)

        self.transaction_size = len(all_transactions)
        self.minimum_support = len(all_transactions) * self.minimum_support

        # Remove
        for item, support in list(items.items()):
            if support < self.minimum_support:
                del items[item]

        def get_support(nodes):
            return sum(n.count for n in nodes)

        def find_with_suffix(tree, suffix):
            for item, nodes in list(tree.items()):
                # add for support 
                support = get_support(nodes)
                if support >= self.minimum_support and item not in suffix:
                    found_set = [item] + suffix
                    yield (found_set, support) if include_support else found_set
                    cond_tree = self.build_conditional_tree(tree.prefix_paths(item))
                    # search freq itemsets in conditional tree
                    # expand found
                    for s in find_with_suffix(cond_tree, found_set):
                        yield s  

        master = maintree()
        # add trans in tree
        for transaction in all_transactions:
            # del infreq
            for index, item in enumerate(transaction):
                if item not in items:
                    del transaction[index]
            # sort count 
            transaction.sort(key=lambda v: items[v], reverse=True)
            master.insert(transaction)

        for itemset in find_with_suffix(master, []):
            yield itemset

    def build_conditional_tree(self, paths):
        # cond tree 
        tree = maintree()
        condition_item = None
        items = set()

        def get_support():
            return sum(n.count for n in tree.nodes(item))

        # count of the leaf node 
        for path in paths:
            if not condition_item:
                # condition_item -> last item in the first path,
                condition_item = path[-1].item

            point = tree.root
            for node in path:
                    # child of node.item
                next_point = point.search(node.item)
                if not next_point:
                    items.add(node.item)
                    # only correct count of condition item 
                    count = node.count if node.item == condition_item else 0
                    next_point = treenode(tree, node.item, count)
                    point.add(next_point)
                    tree._update_route(next_point)
                point = next_point

        # counts of other nodes
        for path in tree.prefix_paths(condition_item):
            count = path[-1].count
            for node in reversed(path[:-1]):
                node._count += count

        # remv nodes infrequent.
        for item in items:
            support = get_support()
            if support < self.minimum_support:
                for node in tree.nodes(item):
                    if not node.parent:
                        node.parent.remove(node)
        #final remv
        for node in tree.nodes(condition_item):
            if not node.parent:  
                node.parent.remove(node)

        return tree


class maintree(object):
    Route = namedtuple('Route', 'head tail')

    def __init__(self):
        self._root = treenode(self, None, None)

        # linked list of every nodes
        self._routes = {}

    @property
    def root(self):
        return self._root

    def insert(self, transaction):
        point = self._root
        # highest sup count one
        for item in transaction:
            next_point = point.search(item)
            if next_point:
                # increment 
                next_point.increment()
            else:
                next_point = treenode(self, item)
                point.add(next_point)
                self._update_route(next_point)
            point = next_point

    def _update_route(self, point):
        # _routes  {'C':(head,tail)}

        if point.item in self._routes:
            route = self._routes[point.item]
            route[1].neighbor = point  # route[1] is the tail
            self._routes[point.item] = self.Route(route[0], point)
        else:
            # new route first node 
            self._routes[point.item] = self.Route(point, point)

    def items(self):
        # should yields ('C', linked list of C)
        for item in self._routes.keys():
            yield (item, self.nodes(item))

    def nodes(self, item):
        if item in self._routes and len(self._routes[item]) >= 1:
            node = self._routes[item][0]
        else:
            return
        while node:
            yield node
            node = node.neighbor

    def prefix_paths(self, item):
        # collect path from ending node to root
        def collect_path(node):
            path = []
            while node and not node.isRoot:
                path.append(node)
                node = node.parent
            # for sup in descending order
            path.reverse()
            return path

        return (collect_path(node) for node in self.nodes(item))

    def cleanup(self, node):
        # clean when node removed
        head, tail = self._routes[node.item]
        if node is head:
            if node is tail or not node.neighbor:
                del self._routes[node.item]
            else:
                self._routes[node.item] = self.Route(node.neighbor, tail)
        else:
            for n in self.nodes(node.item):
                if n.neighbor is node:
                    n.neighbor = node.neighbor  
                    if node is tail:
                        self._routes[node.item] = self.Route(head, n)
                    break

class treenode(object):
    
    def __init__(self, tree, item, count=1):
        self._tree = tree
        self._item = item
        self._count = count
        self._children = {}
        self._parent = None
        self._neighbor = None

    def add(self, child):
        if child.item not in self._children:
            self._children[child.item] = child
            child.parent = self

    def increment(self):
        self._count += 1

    def search(self, item):
        # check child
        if item in self._children:
            return self._children[item]
        else:
            return None

    def remove(self, child):
        del self._children[child.item]
        child.parent = None
        self._tree.cleanup(child)
        for sub_child in child.children:
            if sub_child.item in self._children:
                # add sub's count to child's
                self._children[sub_child.item]._count += sub_child.count
                sub_child.parent = None  # it's an orphan now
            else:
                # here sub-child -> child.
                self.add(sub_child)
        child._children = {}

    def parent():
        def fget(self):
            return self._parent

        def fset(self, value):
            self._parent = value
        return locals()
    parent = property(**parent())
    

    def neighbor():
        def fget(self):
            return self._neighbor
        def fset(self, value):
            self._neighbor = value
        return locals()
    neighbor = property(**neighbor())

    def __contains__(self, item):
        return item in self._children

    @property
    def tree(self):
        return self._tree

    @property
    def item(self):
        return self._item

    @property
    def count(self):
        return self._count

    @property
    def isRoot(self):
        return not self._item and not self._count

    @property
    def leaf(self):
        return len(self._children) == 0

    @property
    def children(self):
        return tuple(self._children.itervalues())

if __name__ == '__main__':
#    begin1=time.time()
    #!!you can change into any number in (0,1)
    f = fp(0.5)
    f.run()
    f.printResults()

    # !!add # below if don't want csv file
    f.writeResults()
#    stop1=time.time()
#    print ('fp takes',(stop1-begin1))
