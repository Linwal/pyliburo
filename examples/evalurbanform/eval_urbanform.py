import time
import pyliburo
import read_collada_4_evalurbanform as read_collada

dae_file = "F:\\kianwee_work\\smart\\journal\\mdpi_sustainability\\case_study\\dae\\grid_tower.dae"

#==================================================================================================
#read and sort collada file
#==================================================================================================
print "READING COLLADA ..."
time1 = time.clock()

closegeoms, opengeom_shells, opengeom_faces, edges = read_collada.read_collada(dae_file)
solid_list = pyliburo.py3dmodel.construct.make_shell_frm_faces(closegeoms)
if opengeom_shells:
    oshell_list = pyliburo.py3dmodel.construct.make_shell_frm_faces(opengeom_shells)

boundary = opengeom_faces[-1]
nfaces = len(opengeom_faces)
plots = opengeom_faces[0:nfaces-1]
time2 = time.clock()
eta1 = time2-time1
print "ETA1:", eta1
#==================================================================================================
#calculate RDI
#==================================================================================================
print "CALCULATING RDI ..."
time3 = time.clock()

#rdi,rdi_percent,dplots,pplots,fplots,total_route_directness_aplot, edges4_networkx, circles_peri_pts  = pyliburo.urbanformeval.route_directness(edges, plots, boundary, route_directness_threshold = 1.6)
pyliburo.urbanformeval.route_directness(edges, plots, boundary, route_directness_threshold = 1.6)                                                                                                  
                                                                                                   
time4 = time.clock()
eta2 = time4-time3
print "ETA2:", eta2

#VISUALISE
display2dlist = []
display2dlist.append(nedges)
display2dlist.append(peripts)
display2dlist.append(errpts)
#display2dlist.append(solid_list)
#display2dlist.append([opengeom_faces[-1]])
#display2dlist.append(edges)
colourlist = ["BLACK", "BLUE", "RED"]
pyliburo.py3dmodel.construct.visualise(display2dlist, colourlist )

#print len(faces), len(edges)