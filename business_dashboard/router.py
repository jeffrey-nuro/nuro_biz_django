import biz_tools
import json
import time
import logging
from heap import Heap
from convex_hull import convexHull
lldist = biz_tools.latlngdist
inf = 1e20

class Router:
    """This class is responsible for loading an OSM map, and handling queries
    for shortest path and reachable region."""

    def __init__(self, zone):
        self._load_map(zone)

    def _load_map(self, zone):
        """Loads an OSM map into memory

        params:
            zone: a string describing the map file to use (for now must be mtv)
        """
        start_time = time.time()
        def way_speed(way):
            if 'maxspeed' not in way.tags: return 25.
            else:
                return float(way.tags['maxspeed'].strip().split(' ')[0])

        self.heuristic_max_speed = 70.
        self.node_dict, good_ways, all_ways = biz_tools.load_map_data(zone)
        self.good_ways = all_ways
        self.good_nids = {}
        self.edges = {}

        seen_nid = {}

        for way in self.good_ways:
            nids = way.nodes
            self.good_nids[nids[0]] = 1
            self.good_nids[nids[-1]] = 1
            for nid in nids:
                if nid in seen_nid:
                    self.good_nids[nid] = 1
                seen_nid[nid] = 1

        for way in self.good_ways:
            last_point = self.node_dict[way.nodes[0]]
            cur_dist = 0.
            cur_nid = way.nodes[0]
            count = 0
            bidirectional = 'oneway' not in way.tags or way.tags['oneway'] == 'no'
            speed_limit = way_speed(way)
            for nid in way.nodes[1:]:
                new_point = self.node_dict[nid]
                # We use time (sec) as our routing distance metric,
                # but store the distance and compute time later
                cur_dist += lldist(last_point, new_point)

                last_point = new_point
                if nid in self.good_nids:
                    count += 1
                    if cur_nid not in self.edges:
                        self.edges[cur_nid] = {}
                    self.edges[cur_nid][nid] = (cur_dist, speed_limit)
                    if bidirectional:
                        if nid not in self.edges:
                            self.edges[nid] = {}
                        self.edges[nid][cur_nid] = (cur_dist, speed_limit)
                    cur_dist = 0.
                    cur_nid = nid

        logging.info('init took %s seconds', time.time() - start_time)

    def _nearest_nid(self, ll):
        min_dist = inf
        best_nid = None
        for nid in self.good_nids:
            new_dist = lldist(self.node_dict[nid], ll)
            if new_dist < min_dist:
                min_dist = new_dist
                best_nid = nid
        return best_nid

    def _dijkstra_step(self, s_heap, s, vis, prev, params, heuristic_dest):
        """
        We abstract this so that we can use similar logic for shortest path and region finding

        Args:
            s_heap: a min_heap of (distance_guess, node)
            s: a dictionary of distance_guess
            prev: previous node dict for shortest path reconstruction
            params: speed limit parameters
            heuristic_dest: goal for shortest path, used for an A*-like heuristic

        Returns:
            next (distance, node) marked for certain in dijkstra's algorithm
        """

        speed_thresh = params['road_speed_thresh_mph'] + 1e-5
        robot_max_speed = params.get('robot_max_speed_mph')

        if robot_max_speed is None: robot_max_speed = speed_thresh
        assert robot_max_speed > 1
        assert speed_thresh < self.heuristic_max_speed

        if len(s_heap.a) == 0: return None, None
        min_s, best_nid = s_heap.pop()
        if min_s > inf/2: return None, None

        vis[best_nid] = 1
        if best_nid in self.edges:
            for nid in self.edges[best_nid]:
                if nid in vis:
                    continue
                dist, speed_limit = self.edges[best_nid][nid]
                if speed_limit > speed_thresh: continue
                edge_dist = dist / min(speed_limit, robot_max_speed) * 3600
                # Using an A* heuristic helps a bit
                if heuristic_dest is not None:
                    edge_dist += (lldist(self.node_dict[nid], self.node_dict[heuristic_dest]) -
                            lldist(self.node_dict[best_nid], self.node_dict[heuristic_dest])) / self.heuristic_max_speed * 3600
                new_s = min_s + edge_dist
                if new_s < s[nid]:
                    old_heap_elem = (s[nid], nid)
                    new_heap_elem = (new_s, nid)
                    if old_heap_elem in s_heap.ind_dict:
                        s_heap.decrease(old_heap_elem, new_heap_elem)
                    else:
                        s_heap.push(new_heap_elem)
                    s[nid] = new_s
                    prev[nid] = best_nid

        return min_s, best_nid

    def _shortest_path(self, n1, n2, params):
        """Standard A* algorithm, with min_heap for ElogV ~ V run time
            Args:
                n1: nid of starting location
                n2: nid of ending location
                params: speed limit parameters

            Returns: distance, [node sequence]
        """

        assert n1 in self.good_nids and n2 in self.good_nids
        s = {nid: inf for nid in self.good_nids}
        s_heap = Heap()
        s[n1] = 0.
        s_heap.push((0., n1))
        vis = {}
        prev = {n1: None}
        while n2 not in vis:
            min_s, best_nid = self._dijkstra_step(s_heap, s, vis, prev, params, n2)
            if best_nid is None:
                break

        if n2 not in prev:
            return inf, []
        node_seq = []
        cur_node = n2
        while cur_node is not None:
            node_seq.append(cur_node)
            cur_node = prev[cur_node]

        traffic_multiplier = params['traffic_multiplier']
        return s[n2] * traffic_multiplier, node_seq[::-1]

    def reachable_region(self, ll, radius, params):
        """Computes set of reachable points and their convex hull

        Args:
            ll: user-defined source
            radius: shortest path distance (in seconds)
            params: speed limit params

        Returns:
            [reachable points for each speed limit], [convex hull for each speed limit]
        """

        n1 = self._nearest_nid(ll)
        start_time = time.time()
        reachable_nids = []
        s = {nid: inf for nid in self.good_nids}
        s_heap = Heap()
        s[n1] = 0.
        s_heap.push((0., n1))
        vis = {}
        prev = {n1: None}
        while True:
            min_s, best_nid = self._dijkstra_step(s_heap, s, vis, prev, params, None)
            if min_s is None or min_s > radius: break
            reachable_nids.append(best_nid)

        logging.info('reachable region within %s seconds found in time %s',
                radius, time.time() - start_time)

        all_points = [self.node_dict[i] for i in reachable_nids]
        hull = convexHull(all_points) if len(all_points) > 2 else []
        return all_points, hull

    def route(self, ll1, ll2, params):
        """Computes shortest path between ll1 and ll2"""
        start_time = time.time()
        n1, n2 = self._nearest_nid(ll1), self._nearest_nid(ll2)
        dist, seq = self._shortest_path(n1, n2, params)
        lls = [] if seq == [] else [ll1] + [self.node_dict[i] for i in seq] + [ll2]
        logging.info('route from %s to %s took %s seconds', n1, n2, time.time() - start_time)
        return dist, lls

if __name__ == '__main__':
    router = Router(True)
    params = {'num_robots': 3, 'business_prep_time_min': 20, 'customer_pickup_time_min': 5,
            'num_requests': 100, 'business_radius_mi': 2, 'robot_start': 'random',
            'robot_max_speed_mph': 50., 'road_speed_thresh_mph': 50, 'traffic_multiplier': 1.}
    lls, hull = router.reachable_region([37.390729233381265, -122.10464061596184], 180, params)
    logging.info(lls)
    #with open('static/js/debug_points.js', 'w') as f:
    #    f.write('var debug_points = ' + json.dumps(lls))
