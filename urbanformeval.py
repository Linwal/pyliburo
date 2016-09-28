# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
import py3dmodel

def calculate_srfs_area(occ_srflist):
    area = 0
    for srf in occ_srflist:
        area = area + py3dmodel.calculate.face_area(srf)
        
    return area
    
def pyptlist2vertlist(pyptlist):
    vertlist = []
    for pypt in pyptlist:
        vert = py3dmodel.construct.make_vertex(pypt)
        vertlist.append(vert)
    return vertlist
    
    
def frontal_area_index(facet_occpolygons, plane_occpolygon, wind_dir):
    '''
    Algorithm to calculate frontal area index
    
    PARAMETERS
    ----------
    :param facet_occpolygons : a list of occ faces of vertical facades 
    :ptype: list(occface)
    
    :param plane_occpolygon: an occ face that is the horizontal plane buildings are sitting on 
    :ptype: occface
    
    :param wind_dir: a 3d tuple specifying the direction of the wind
    :ptype: tuple
    
    RETURNS
    -------
    :returns fai: frontal area index 
    :rtype: float
    
    :returns fuse_srfs: the projected surfaces fused together
    :rtype: list(occface)
    
    :returns projected_facet_faces: the projected surfaces not fuse together
    :rtype: list(occface)
    
    :returns wind_plane: the plane representing the direction of the wind
    :rtype: occface
    
    :returns surfaces_projected: the facade surfaces that are projected
    :rtype: list(occface)
    
    '''
    facet_faces_compound = py3dmodel.construct.make_compound(facet_occpolygons)
     
    #create win dir plane
    #get the bounding box of the compound, so that the wind plane will be placed at the edge of the bounding box
    xmin, ymin, zmin, xmax, ymax, zmax = py3dmodel.calculate.get_bounding_box(facet_faces_compound)
    pymidpt = py3dmodel.calculate.get_centre_bbox(facet_faces_compound)
    #calculate the furthest distance of the bounding box
    pycornerpt = (xmin, ymin, 0)
    
    furtherest_dist = py3dmodel.calculate.distance_between_2_pts(pymidpt, pycornerpt)
    #create the wind plane 
    pt4plane = py3dmodel.modify.move_pt(pymidpt, wind_dir, furtherest_dist) 
    wind_plane = py3dmodel.construct.make_plane_w_dir(pt4plane, wind_dir)
    
    surfaces_projected = []
    projected_facet_faces = []
    for facet_face in facet_occpolygons:
        srf_dir = py3dmodel.calculate.face_normal(facet_face)
        #srf_midpt = py3dmodel.calculate.face_midpt(urb_face)
        angle = py3dmodel.calculate.angle_bw_2_vecs(wind_dir, srf_dir)
        #interpt, interface = py3dmodel.calculate.intersect_shape_with_ptdir(wind_plane, srf_midpt, srf_dir)
        if angle<90:
            surfaces_projected.append(facet_face)
            projected_pts = py3dmodel.calculate.project_face_on_faceplane(wind_plane, facet_face)
            projected_srf = py3dmodel.construct.make_polygon(py3dmodel.fetch.occptlist2pyptlist(projected_pts))
            if py3dmodel.calculate.face_area(projected_srf) >0:
                projected_facet_faces.append(projected_srf)
         
    npfaces = len(projected_facet_faces)
    if npfaces == 1:
        fuse_srfs = projected_facet_faces
    else:
        for psrf_cnt in range(npfaces-1):
            if psrf_cnt ==0:
                fuse_shape = py3dmodel.construct.boolean_fuse(projected_facet_faces[psrf_cnt], projected_facet_faces[psrf_cnt+1])
            else:
                fuse_shape = py3dmodel.construct.boolean_fuse(fuse_shape, projected_facet_faces[psrf_cnt+1])
                
        fuse_compound = py3dmodel.fetch.shape2shapetype(fuse_shape) 
        fuse_srfs = py3dmodel.fetch.geom_explorer(fuse_compound,"face")
    
    #calculate the frontal area index
    facet_area = calculate_srfs_area(fuse_srfs)
    plane_area = py3dmodel.calculate.face_area(plane_occpolygon)
    fai = facet_area/plane_area
    
    return fai, fuse_srfs, projected_facet_faces, wind_plane, surfaces_projected
    
def route_directness(network_occedgelist, plot_occfacelist, boundary_occface, obstructions_occshapelist = None, route_directness_threshold = 1.6):
    import networkx as nx
    '''
    Algorithm for Route Directness Test  
    Stangl, P.. 2012 the pedestrian route directness test: A new level of service model.
    urban design international 17, 228-238
    
    A test that measures the connectivity of street network in a neighbourhood
    measuring route directness for each parcel to each of a series
    of points around the periphery of the study area,
    and identifying the percentage of parcels for which
    any of these measures exceed 1.6. Urban area is 1.3, suburban is 1.6
    
    PARAMETERS
    ----------
    :param network_occedgelist : a list of occedges that is the network to be analysed
    :ptype: list(occedge)
    
    :param plot_occfacelist: a list of occfaces that is the land use plots
    :ptype: list(occface)
    
    :param boundary_occface: occface that is the boundary of the area
    :ptype: occface
    
    :param route_directness_threshold: a float specifying the route directness threshold, default value 1.6
    :ptype: float
    
    RETURNS
    -------
    :returns route_directness_measure: route_directness_measure
    :rtype: float
    
    :returns failed_plots: plots that fail the route directness measure
    :rtype: list(occface)
    
    :returns successful_plots: plots that pass the route directness measure
    :rtype: list(occface)
    
    :returns peripheral_pts: peripheral pts
    :rtype: list(occpts)
    
    '''
    #calculate the peripheral points
    #get all the intersection points 
    #extract the wire from the face and convert it to a bspline curve
    displaylist = []
    boundary_pyptlist = py3dmodel.fetch.pyptlist_frm_occface(boundary_occface)
    boundary_pyptlist.append(boundary_pyptlist[0])
    bedge = py3dmodel.construct.make_bspline_edge(boundary_pyptlist, degree=1)
    boundary_occwire = py3dmodel.fetch.wires_frm_face(boundary_occface)[0]
    boundary_occedgelist = py3dmodel.fetch.edges_frm_wire(boundary_occwire)
    interptlist = []
    for network_occedge in network_occedgelist:
        intersect_pts = py3dmodel.calculate.intersect_edge_with_edge(bedge, network_occedge, tolerance=1e-02)
        if intersect_pts!=None:
            interptlist.extend(intersect_pts)
            
    fused_interptlist = py3dmodel.modify.fuse_pts(interptlist)
    ulist = []
    for fused_interpt in fused_interptlist:
        parmu = py3dmodel.calculate.pt2edgeparameter(fused_interpt,bedge)
        ulist.append(parmu)
    
    ulist = sorted(ulist)
    print ulist
    length = py3dmodel.calculate.edgelength(ulist[0],ulist[1], bedge)
    trimmed_edge = py3dmodel.modify.trimedge(ulist[8], ulist[9], bedge)
    tmid = py3dmodel.calculate.edge_midpt(trimmed_edge)
    fused_interptlist.append(tmid)

    displaylist.append(trimmed_edge)
    displaylist.extend(network_occedgelist)
    displaylist.extend(py3dmodel.fetch.pyptlist2vertlist(fused_interptlist))
    return displaylist
    
    #construct a network with the edges 