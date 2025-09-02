from collections import defaultdict

class Layout():
    def __init__(self,model):
        self.model = model
        self.positions = self._calculate_positions_from_model()
        point = self._compute_max_corrdinate(self.positions)
        self.max = (point[0]+1.5, point[1]+1.5)
        
    def _calculate_positions_from_model(self):
        if self.model.istar_positions and not self.model.positions:
            # Reverse y so that root is on top
            positions = self.model.istar_positions.copy()
            max_y = max(pos[1] for pos in positions.values()) + 25 + 70
            for k in positions:
                positions[k] = (positions[k][0], max_y - positions[k][1])
            # Remove x-offset
            min_x = min(pos[0] for pos in positions.values()) - 25 - 45
            for k in positions:
                positions[k] = (positions[k][0]-min_x, positions[k][1])
            scale = 1/50           
            for k in positions:
                positions[k] = (positions[k][0]*scale, positions[k][1]*scale)
            self.model.positions = positions
            return positions
        elif not self.model.positions:
            links = [ (link[0],link[1]) for link in self.model.links]
            return self._calculate_positions(links,min_coord=0.7)
        return self.model.positions
    
    def _compute_max_corrdinate(self,ps):
        return (max([p[0] for p in ps.values()]), max([p[1] for p in ps.values()]))
        
    def _calculate_positions(self, links, y_gap=2.0, x_gap=2.0, min_coord=2.0):
        """
        Compute positions for nodes based on hierarchical links.

        Args:
            links (list of tuples): Each tuple is (parent, child).
            y_gap (int): Vertical distance between levels.
            x_gap (int): Horizontal distance between nodes.
            min_coord (int): Minimum x and y coordinate for all nodes.

        Returns:
            dict: Mapping of node -> (x, y) positions.
        """
        # Build parent -> children mapping
        children = defaultdict(list)
        parents = defaultdict(list)
        all_nodes = set()
        for parent, child in links:
            children[parent].append(child)
            parents[child].append(parent)
            all_nodes.update([parent, child])

        # Identify roots (nodes with no parents)
        roots = [n for n in all_nodes if n not in parents]

        positions = {}
        x_counter = [0]  # mutable counter for horizontal spacing

        # Recursive function to assign positions
        def assign_positions(node, depth=0):
            if node not in children or not children[node]:
                # Leaf node: assign next x position
                x = x_counter[0] * x_gap
                positions[node] = (x, depth * y_gap)
                x_counter[0] += 1
            else:
                child_xs = []
                for child in children[node]:
                    assign_positions(child, depth + 1)
                    child_xs.append(positions[child][0])
                # Parent is centered above its children
                x = sum(child_xs) / len(child_xs)
                positions[node] = (x, depth * y_gap)

        # Assign positions for each root
        for root in roots:
            assign_positions(root)

        # Shift x-coordinates so minimum is min_coord
        min_x = min(pos[0] for pos in positions.values())
        min_y = min(pos[1] for pos in positions.values())
        for k in positions:
            positions[k] = (
                positions[k][0] - min_x + min_coord,
                positions[k][1] - min_y + min_coord
            )

        # Reverse y so that root is on top
        max_y = max(pos[1] for pos in positions.values())
        for k in positions:
            positions[k] = (positions[k][0], max_y - positions[k][1] + min_coord)

        return positions