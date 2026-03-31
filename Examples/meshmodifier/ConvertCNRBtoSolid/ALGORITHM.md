# CNRB to Solid Cylinder Conversion Algorithm

## Overview

This algorithm converts LS-DYNA `*CONSTRAINED_NODAL_RIGID_BODY` (CNRB) definitions into solid hexahedral (hexa8) mesh cylinders. CNRB is commonly used to model bolted connections in FE models, but for explicit dynamic simulations (e.g., drop tests), replacing CNRB with actual solid elements provides more realistic deformation behavior.

## Input

- **CNRB definition**: PID, NSID (node set ID), PNODE (center/pilot node)
- **Node set**: Nodes surrounding a cylindrical hole at various Z-heights
- **Material properties**: E, PR, RHO for the new solid elements

## Output

- Solid hexa8 cylinder mesh (O-grid topology)
- `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET` connecting original hole nodes to new cylinder
- CNRB removed, center node removed

---

## Algorithm Steps

### Step 1: Axis Direction Detection (PCA)

The cylinder axis is determined automatically using Principal Component Analysis.

```
Input: N nodes surrounding the hole
1. Compute centroid of all nodes (or use PNODE if available)
2. Subtract centroid from all node coordinates
3. Compute 3x3 covariance matrix
4. Eigendecomposition → largest eigenvalue's eigenvector = axis direction
```

This works because the nodes span the most distance along the cylinder axis (Z-direction), so the largest variance direction = axis.

**Fallback**: User can specify `AxisDirection=X/Y/Z` explicitly.

### Step 2: Cylindrical Coordinate Transformation

Each node is converted from Cartesian (x,y,z) to cylindrical (R, θ, Z_local):

```
For each node:
    vec = node_position - center
    Z_local = dot(vec, axis)           # projection onto axis
    radial = vec - Z_local * axis       # perpendicular component
    R = norm(radial)                    # distance from axis
    θ = atan2(dot(radial, perp2), dot(radial, perp1))
```

Where `perp1`, `perp2` are two orthogonal vectors perpendicular to the axis:
```
if abs(axis[2]) < 0.9:
    perp1 = normalize(cross(axis, [0,0,1]))
else:
    perp1 = normalize(cross(axis, [1,0,0]))
perp2 = cross(axis, perp1)
```

### Step 3: Z-Level Grouping

Nodes are grouped by their Z_local values with a tolerance:

```
1. Round each Z_local to nearest multiple of ZTolerance
2. Group nodes with same rounded Z value
3. Result: {z_level: [nodes at this height]}
```

### Step 4: R-Value Clustering (Multi-Radius Support)

Within each Z-level, nodes may have different R values (e.g., stepped bolt with narrow shaft + wide head). These are separated:

```
For each Z-level:
    Sort nodes by R
    Cluster: split where R_gap > RTolerance
    Result: [(R_avg, [nodes_in_cluster])]
```

This produces "cylinder chains" — groups of Z-levels with similar R values:
```
Chain 1 (R~1.5): Z=0, Z=2, Z=4, Z=6
Chain 2 (R~3.0): Z=4, Z=6, Z=8, Z=10
```

### Step 5: Conformal Mesh Strategy

**Key insight**: Build the full cylinder at R_max, then omit elements beyond local R at each Z-level.

```
R_max = max R across all Z-levels
R_min = min R across all Z-levels

Ring structure:
    Core: O-grid square (size = R_min * core_ratio)
    Ring 1: core_boundary → R1
    Ring 2: R1 → R2
    ...
    Ring N: R_{N-1} → R_max

Nodes: Created at ALL ring radii for ALL Z-levels
Elements: Created only where ring_radius <= local_R at that Z-layer
```

This guarantees conformal mesh at R transitions because:
- All nodes exist at all Z-levels (same grid structure)
- Only element creation is conditional
- Shared nodes between layers ensure connectivity

### Step 6: O-Grid (Butterfly Mesh) Cross-Section

The cylinder cross-section uses an O-grid topology for all-hexa meshing:

```
         ○─○─○─○─○
        /           \
       ○  □─□─□─□  ○
       |  | | | |  |
       ○  □─□─□─□  ○     □ = core nodes (regular grid)
       |  | | | |  |     ○ = outer ring nodes (circular)
       ○  □─□─□─□  ○
        \           /
         ○─○─○─○─○
```

For N circumferential nodes (must be divisible by 4):
- `m = N / 4` (segments per quadrant)
- **Core**: `(m+1) × (m+1)` regular grid, side = `R * core_ratio * 2`
- **Outer ring**: N nodes on circle at radius R
- **Core elements**: `m × m` hexa per Z-layer
- **Shell elements**: N hexa connecting core boundary to outer ring

#### Core Node Coordinates
```
d = R * core_ratio  (half-side of core square)
For i in [0, m], j in [0, m]:
    x_local = -d + 2*d*i/m
    y_local = -d + 2*d*j/m
    position = center + Z*axis + x_local*perp1 + y_local*perp2
```

#### Outer Ring Node Coordinates
```
theta_offset = 5π/4  (aligned with core corner at (-d,-d))
For k in [0, N):
    θ = theta_offset + 2πk/N
    position = center + Z*axis + R*(cos(θ)*perp1 + sin(θ)*perp2)
```

#### Core-to-Ring Boundary Mapping

The core boundary is traversed CCW starting from corner (0,0):
```
Bottom:  (0,0)→(1,0)→...→(m,0)       [m segments]
Right:   (m,0)→(m,1)→...→(m,m)       [m segments]
Top:     (m,m)→(m-1,m)→...→(0,m)     [m segments]
Left:    (0,m)→(0,m-1)→...→(0,1)     [m segments]
Total: 4m = N segments → matches N outer ring nodes
```

Each boundary segment k maps to outer ring arc (k, k+1).

### Step 7: Hexa Element Node Ordering

LS-DYNA hexa8 requires bottom face CCW when viewed from outside (right-hand rule with normal pointing from bottom to top).

**Core hexa** (bottom face):
```
(i,j) → (i+1,j) → (i+1,j+1) → (i,j+1)
```

**Shell hexa** (bottom face, outer→core):
```
outer[k] → outer[k+1] → core[k+1] → core[k]
```

**Additional ring hexa** (bottom face, outer_ring→inner_ring):
```
ring[ri][k] → ring[ri][k+1] → ring[ri-1][k+1] → ring[ri-1][k]
```

Top face: same ordering at next Z-level.

### Step 8: R-Based Element Filtering

For each Z-layer between z_bot and z_top:
```
R_local = min(R_max_at_z_bot, R_max_at_z_top) * radiusScale

For each ring ri:
    if ring_radii[ri] > R_local * 1.01:  # 1% margin
        break  # skip this and all outer rings
    else:
        create N hexa elements for this ring
```

This produces a stepped cylinder where smaller R sections have fewer radial rings.

### Step 9: Tied Contact Creation

Original CNRB nodes are connected to the new solid cylinder via tied contact:

```
1. Create node set from all original CNRB nodes
2. Create *CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET:
   - SSID = node set (SSTYP=4, node-based)
   - MSID = new solid part ID (MSTYP=3, part-based)
```

This transfers forces between the original mesh and the new bolt mesh.

### Step 10: Cleanup

```
1. Remove CNRB from constrained manager
2. Remove center node (PNODE) from node manager
3. Synchronize max IDs
```

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RadiusScale` | 0.999 | Scale factor for cylinder radius (slightly inside hole) |
| `NumCircumNodes` | auto | Circumferential nodes (0=auto from max nodes per Z-level, rounded to multiple of 4) |
| `InnerRadiusRatio` | 0.3 | Core square size relative to R (core_side = 2*R*ratio) |
| `AxisDirection` | Auto | Cylinder axis (Auto=PCA, or X/Y/Z) |
| `ZTolerance` | 0.01 | Z-level grouping tolerance (mm) |
| `RTolerance` | 0.5 | R-value clustering tolerance for multi-radius detection (mm) |
| `E` | 2e11 | Young's modulus |
| `PR` | 0.3 | Poisson's ratio |
| `RHO` | 7850 | Density |

## Element Count Formula

For N circumferential nodes, L Z-layers, T total radial rings, T_local rings at each layer:

```
Core elements per layer: (N/4)^2
Ring elements per layer per ring: N
Total = sum over layers: (N/4)^2 + N * T_local[layer]
```

Example (N=12, 7 Z-layers, 3 rings, 4 layers at full R):
- Core: 9 per layer × 7 layers = 63
- Ring: 12 × T_local per layer
- If 3 layers have 1 ring, 4 layers have 3 rings:
  - 3 × 12 × 1 = 36
  - 4 × 12 × 3 = 144
- Total = 63 + 36 + 144 = 243

## Key Design Decisions

1. **R_max-first approach**: Build at maximum radius, omit outer elements for smaller R sections. This guarantees conformal mesh because all nodes share the same angular grid.

2. **O-grid topology**: Avoids degenerate elements at center (no wedge/pyramid elements). All elements are proper hexa8 with positive Jacobian.

3. **PCA axis detection**: Works for arbitrary orientation bolts without user intervention.

4. **Tied contact instead of node merging**: The original mesh nodes and new cylinder nodes are at slightly different R (radiusScale=0.999), so direct node sharing isn't possible. Tied contact provides the force transfer.

5. **CNRB PID reuse**: The new solid part gets the same PID as the original CNRB, maintaining the ID namespace consistency.

## Configuration File Format

```
*Mode
CONVERT_CNRB_TO_SOLID,1
**ConvertCNRBtoSolid,1
ALL,True
E,200000000000
PR,0.3
RHO,7850
RadiusScale,0.999
NumCircumNodes,8
AxisDirection,Auto
InnerRadiusRatio,0.3
ZTolerance,0.01
RTolerance,0.5
**EndConvertCNRBtoSolid
*End
```

## Limitations

- Assumes cylindrical hole geometry (not elliptical or irregular)
- PNODE must be at or near the cylinder axis
- All nodes in NSID are assumed to belong to the same bolt hole
- Does not handle tapered transitions (uses step function at R boundaries)
- Orphan nodes from ring generation at Z-levels where R < R_max are not removed (harmless but wasteful)
