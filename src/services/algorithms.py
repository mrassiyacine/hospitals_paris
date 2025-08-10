import heapq


def dijkstra_nearest_hospital(graph: dict, start: int, hospitals: set):
    """
    Dijkstra's algorithm to find the shortest path in a graph.
    Args:
        graph (dict): The graph represented as an adjacency list; {node: [(neighbor, length), ...]}
        start (int): The starting node.
        hospitals (set): A set of hospital node IDs to consider as endpoints.
    Returns:
        hospital_node (int): The nearest hospital node ID.
        path (list): The path taken to reach the hospital.
        distance (float): The total distance to the nearest hospital.
    """
    queue = [(0, start, [])]  # (distance, current_node, path)
    seen = set()
    while queue:
        current_distance, current_node, path = heapq.heappop(queue)
        if current_node in seen:
            continue
        path = path + [current_node]
        if current_node in hospitals:
            return current_node, path, current_distance
        seen.add(current_node)
        for neighbor, length in graph.get(current_node, []):
            if neighbor not in seen:
                heapq.heappush(queue, (current_distance + length, neighbor, path))
    return None, [], float("inf")
