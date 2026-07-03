# 디스크리트 샌드위치 검증: 고정 삼각형 스킨 2장 사이 버퍼를 gmsh로 tet 메싱, 노드 태그 보존 + 혼합요소(hexa+pyr+tet) msh 출력 확인
import numpy as np
import gmsh

def cube_tris(center, half, node_tag_start, invert=False):
    """Return (coords dict tag->xyz, tris list of node-tag triples) for a triangulated cube."""
    c = np.array(center, float); h = half
    corners = np.array([[sx, sy, sz] for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)], float)
    pts = c + h * corners  # order: (---),(+--),(-+-),(++-),(--+),(+-+),(-++),(+++)
    tags = list(range(node_tag_start, node_tag_start + 8))
    # 12 tris, outward orientation
    quads = [
        (0, 2, 3, 1),  # z- (down, outward -z)
        (4, 5, 7, 6),  # z+
        (0, 1, 5, 4),  # y-
        (2, 6, 7, 3),  # y+
        (0, 4, 6, 2),  # x-
        (1, 3, 7, 5),  # x+
    ]
    tris = []
    for q in quads:
        a, b, cc, d = [tags[i] for i in q]
        tris += [(a, b, cc), (a, cc, d)]
    if invert:
        tris = [(a, cc, b) for (a, b, cc) in tris]
    return dict(zip(tags, pts)), tris

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("sandwich")

# Outer cube (half=10, tags 1..8, outward normals) and inner cube (half=4, tags 101..108, inverted = normals toward gap)
outer_nodes, outer_tris = cube_tris((0, 0, 0), 10.0, 1, invert=False)
inner_nodes, inner_tris = cube_tris((0, 0, 0), 4.0, 101, invert=True)

s_out = gmsh.model.addDiscreteEntity(2)
s_in = gmsh.model.addDiscreteEntity(2)

def add_skin(surf, nodes, tris):
    tags = list(nodes.keys())
    coords = np.concatenate([nodes[t] for t in tags])
    gmsh.model.mesh.addNodes(2, surf, tags, coords)
    etags = []  # let gmsh pick element tags: must supply; use offset
    flat = [n for tri in tris for n in tri]
    gmsh.model.mesh.addElementsByType(surf, 2, [], flat)  # type 2 = 3-node triangle

add_skin(s_out, outer_nodes, outer_tris)
add_skin(s_in, inner_nodes, inner_tris)

# Surface loop + volume (geo kernel referencing discrete surfaces)
loop_out = gmsh.model.geo.addSurfaceLoop([s_out])
loop_in = gmsh.model.geo.addSurfaceLoop([s_in])
vol = gmsh.model.geo.addVolume([loop_out, loop_in])
gmsh.model.geo.synchronize()

gmsh.option.setNumber("Mesh.MeshSizeMin", 2.0)
gmsh.option.setNumber("Mesh.MeshSizeMax", 3.0)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
gmsh.model.mesh.generate(3)

# --- Verification 1: our node tags preserved with identical coords?
ok = True
for tag, xyz in {**outer_nodes, **inner_nodes}.items():
    c, _, _, _ = gmsh.model.mesh.getNode(tag)
    if not np.allclose(c, xyz, atol=1e-12):
        ok = False
        print("MOVED/LOST node", tag, c, xyz)
print("node-tag preservation:", "PASS" if ok else "FAIL")

# --- Verification 2: tets reference our skin tags directly?
etypes, etags, enodes = gmsh.model.mesh.getElements(3, vol)
tets = enodes[0].reshape(-1, 4)
used = set(tets.flatten().tolist())
skin_used = used & set(list(outer_nodes) + list(inner_nodes))
print(f"tets: {len(tets)}, skin tags referenced by tets: {len(skin_used)}/16")

# --- Verification 3: skin triangles unchanged (count) after 3D meshing
for s, tris in ((s_out, outer_tris), (s_in, inner_tris)):
    _, _, en = gmsh.model.mesh.getElements(2, s)
    print(f"surface {s}: tris before {len(tris)}, after {len(en[0]) // 3}",
          "PASS" if len(en[0]) // 3 == len(tris) else "FAIL")

# --- Verification 4: quality
q = gmsh.model.mesh.getElementQualities(etags[0], "minSICN")
print(f"tet minSICN min={q.min():.3f} mean={q.mean():.3f} neg={(q <= 0).sum()}")

# --- Verification 5: mixed-element write. New discrete volume with 1 hexa + 1 pyramid + adopt tets impossible in same
# model cleanly; test standalone mixed model instead.
gmsh.model.add("mixed")
gmsh.model.setCurrent("mixed")
v = gmsh.model.addDiscreteEntity(3)
# hexa 1x1x1 at origin, pyramid on its top face, one tet on a pyramid lateral face
nid = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
    [0.5, 0.5, 1.5],          # pyramid apex (tag 9)
    [0.5, -0.3, 1.6],         # tet extra node (tag 10)
])
gmsh.model.mesh.addNodes(3, v, list(range(1, 11)), nid.flatten())
gmsh.model.mesh.addElementsByType(v, 5, [], [1, 2, 3, 4, 5, 6, 7, 8])       # hexa8
gmsh.model.mesh.addElementsByType(v, 7, [], [5, 6, 7, 8, 9])                # pyramid5
gmsh.model.mesh.addElementsByType(v, 4, [], [5, 6, 9, 10])                  # tet4
out = "/tmp/claude-1000/-home-koopark-serviceApptainers-appt313-opt-pyKooCAE/e47c80d5-8b2e-4820-905b-5c251e2c27e9/scratchpad/airmesh_proto/mixed_test.msh"
gmsh.write(out)
gmsh.open(out)
tot = 0
for et, _, en in zip(*[list(x) for x in gmsh.model.mesh.getElements(3)]):
    name, _, _, nn, _, _ = gmsh.model.mesh.getElementProperties(et)
    print(f"read back: {name} x {len(en) // nn}")
    tot += len(en) // nn
print("mixed write/read:", "PASS" if tot == 3 else "FAIL")
gmsh.finalize()
