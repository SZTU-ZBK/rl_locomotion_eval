"""Scale A1 URDF leg geometry and masses for morphology variants."""

from __future__ import division, print_function

import os
import re
import xml.etree.ElementTree as ET

LEG_PREFIXES = ("FR", "FL", "RR", "RL")
LEG_JOINT_SUFFIXES = ("_hip_joint", "_thigh_joint", "_calf_joint", "_foot_fixed")
LEG_LINK_PATTERN = re.compile(r"^(FR|FL|RR|RL)_(hip|thigh|calf|foot)$")
TRUNK_LINK_NAME = "trunk"


def scale_trunk(tree, scale):
    """Scale trunk collision/visual/inertial with leg scale for consistent morphology."""
    root = tree.getroot()
    for link in root.findall("link"):
        if link.get("name") != TRUNK_LINK_NAME:
            continue
        inertial = link.find("inertial")
        if inertial is not None:
            mass_elem = inertial.find("mass")
            if mass_elem is not None and mass_elem.get("value"):
                mass_elem.set("value", "%.6f" % _scale_mass(float(mass_elem.get("value")), scale))
            origin = inertial.find("origin")
            if origin is not None and origin.get("xyz"):
                origin.set("xyz", _format_xyz(_scale_xyz(_parse_xyz(origin.get("xyz")), scale)))
        for tag in ("collision", "visual"):
            for section in link.findall(tag):
                origin = section.find("origin")
                geom = section.find("geometry")
                if geom is None:
                    continue
                if geom.find("box") is not None:
                    _scale_box_geom(origin, geom, scale)
                mesh = geom.find("mesh")
                if mesh is not None and mesh.get("scale"):
                    mesh.set("scale", "%.6f %.6f %.6f" % (scale, scale, scale))
    return tree


def _parse_xyz(text):
    parts = [float(x) for x in text.strip().split()]
    if len(parts) != 3:
        raise ValueError("Expected xyz with 3 values, got: %s" % text)
    return parts


def _format_xyz(xyz):
    return "%.6f %.6f %.6f" % tuple(xyz)


def _scale_xyz(xyz, scale):
    return [xyz[0] * scale, xyz[1] * scale, xyz[2] * scale]


def _scale_mass(mass_value, scale):
    return mass_value * (scale ** 3)


def _scale_box_size(size_text, scale):
    parts = [float(x) for x in size_text.strip().split()]
    return " ".join("%.6f" % (p * scale) for p in parts)


def _scale_cylinder_geom(origin_elem, geom_elem, scale):
    for attr in ("length", "radius"):
        if geom_elem.get(attr):
            geom_elem.set(attr, "%.6f" % (float(geom_elem.get(attr)) * scale))
    if origin_elem is not None and origin_elem.get("xyz"):
        origin_elem.set("xyz", _format_xyz(_scale_xyz(_parse_xyz(origin_elem.get("xyz")), scale)))


def _scale_box_geom(origin_elem, geom_elem, scale):
    box = geom_elem.find("box")
    if box is not None and box.get("size"):
        box.set("size", _scale_box_size(box.get("size"), scale))
    if origin_elem is not None and origin_elem.get("xyz"):
        origin_elem.set("xyz", _format_xyz(_scale_xyz(_parse_xyz(origin_elem.get("xyz")), scale)))


def _leg_from_joint_name(joint_name):
    for prefix in LEG_PREFIXES:
        if joint_name.startswith(prefix + "_"):
            return prefix
    return None


def _rewrite_mesh_paths(root, mesh_dir):
    mesh_dir = os.path.abspath(mesh_dir)
    if not mesh_dir.endswith(os.sep):
        mesh_dir = mesh_dir + os.sep
    for mesh in root.iter("mesh"):
        filename = mesh.get("filename")
        if not filename:
            continue
        if filename.startswith("../meshes/"):
            mesh.set("filename", mesh_dir + os.path.basename(filename))
        elif filename.startswith("package://"):
            mesh.set("filename", mesh_dir + os.path.basename(filename))


def scale_a1_urdf_tree(tree, leg_scales, mesh_dir):
    root = tree.getroot()
    _rewrite_mesh_paths(root, mesh_dir)

    for joint in root.findall("joint"):
        name = joint.get("name", "")
        leg = _leg_from_joint_name(name)
        if leg is None:
            continue
        scale = leg_scales[leg]
        if any(name.endswith(suffix) for suffix in LEG_JOINT_SUFFIXES):
            origin = joint.find("origin")
            if origin is not None and origin.get("xyz"):
                origin.set("xyz", _format_xyz(_scale_xyz(_parse_xyz(origin.get("xyz")), scale)))

    for link in root.findall("link"):
        name = link.get("name", "")
        match = LEG_LINK_PATTERN.match(name)
        if not match:
            continue
        leg = match.group(1)
        scale = leg_scales[leg]

        inertial = link.find("inertial")
        if inertial is not None:
            mass_elem = inertial.find("mass")
            if mass_elem is not None and mass_elem.get("value"):
                mass_elem.set("value", "%.6f" % _scale_mass(float(mass_elem.get("value")), scale))
            origin = inertial.find("origin")
            if origin is not None and origin.get("xyz"):
                origin.set("xyz", _format_xyz(_scale_xyz(_parse_xyz(origin.get("xyz")), scale)))

        for tag in ("collision", "visual"):
            for section in link.findall(tag):
                origin = section.find("origin")
                geom = section.find("geometry")
                if geom is None:
                    continue
                if geom.find("box") is not None:
                    _scale_box_geom(origin, geom, scale)
                elif geom.find("cylinder") is not None:
                    _scale_cylinder_geom(origin, geom.find("cylinder"), scale)

    scale_trunk(tree, mean_leg_scale(leg_scales))
    return tree


def symmetric_leg_scales(scale):
    return {leg: scale for leg in LEG_PREFIXES}


def full_asym_leg_scales(fr, fl, rr, rl):
    return {"FR": fr, "FL": fl, "RR": rr, "RL": rl}


def mean_leg_scale(leg_scales):
    return sum(leg_scales[p] for p in LEG_PREFIXES) / float(len(LEG_PREFIXES))


def scale_a1_urdf_file(src_path, dst_path, leg_scales, mesh_dir=None):
    if mesh_dir is None:
        mesh_dir = os.path.join(os.path.dirname(os.path.dirname(src_path)), "meshes")
    tree = ET.parse(src_path)
    scale_a1_urdf_tree(tree, leg_scales, mesh_dir)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tree.write(dst_path, encoding="unicode", xml_declaration=True)
