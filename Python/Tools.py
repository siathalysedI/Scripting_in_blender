
__author__ ="Michel Anders (varkenvarken)"
__version__ = "1.0 2009/07/28"
__copyright__ = "(c) 2009 LICENSE YET TO BE DETERMINED"
__url__ = ["author's site, http://www.swineworld.org"]

__doc__ = """\
a collection of Blender tools
"""

import Blender
from copy import deepcopy

def vertexcopy(verts,faces):
	n = len(verts)
	verts = deepcopy(verts)
	faces = [ tuple([t+n for t in face]) for face in faces ]
	return verts,faces

def translate(verts,t):
	return [ (vert[0]+t[0],vert[1]+t[1],vert[2]+t[2]) for vert in verts]

def scalemedian(verts,t):
	n = len(verts)
	mx = sum(v[0] for v in verts)/n
	my = sum(v[1] for v in verts)/n
	mz = sum(v[2] for v in verts)/n
	return [ ((vert[0]-mx)*t[0]+mx,(vert[1]-my)*t[1]+my,(vert[2]-mz)*t[2]+mz) for vert in verts]

def extrude(verts,faces,face,t=(0,0,0),s=(1,1,1),deleteface=True):
	nverts = len(verts)
	newverts = [verts[vert] for vert in face]
	print '***',newverts
	newverts = translate(newverts,t)
	newverts = scalemedian(newverts,s)
	print '***',newverts
	verts.extend(newverts)
	newface = tuple(i+nverts for i in range(len(face)))
	# create connecting faces. Extrude face may be tri or quad, connecting faces are always quads
	for nf in range(len(face)-1):
		faces.append((face[nf],face[nf+1],newface[nf+1],newface[nf]))
		if nf==1 : left = faces[-1]
	faces.append((face[0],newface[0],newface[-1],face[-1]))
	right=faces[-1]
	faces.append(newface)
	if deleteface : faces.remove(face)	
	return verts,faces,left,right

from Blender.Mathutils import Vector as vec

def bridge_edgeloops(e1,e2,verts):
	e1 = e1[:]
	e2 = e2[:]
	faces=[]
	if len(e1) == len(e2) and len(e1) > 0 :
		for a in e1:
			distance = None
			best = None
			enot = []
			while len(e2):
				b = e2.pop(0)
				d1 = (vec(verts[a[0]]) - vec(verts[b[0]])).length + \
			         (vec(verts[a[1]]) - vec(verts[b[1]])).length
				d2 = (vec(verts[a[0]]) - vec(verts[b[1]])).length + \
			         (vec(verts[a[1]]) - vec(verts[b[0]])).length
				if d2<d1 :
					b =(b[1],b[0])
					d1 = d2
				if distance == None or d1<distance :
					if best != None:
						enot.append(best)
					best = b
					distance = d1
				else:
					enot.append(b)
			e2 = enot
			faces.append((a,best))

	return [(a[0],b[0],b[1],a[1]) for a,b in faces]

def closegap(edgeloop,verts):
	v = {}
	for v1,v2 in edgeloop:
		v[v1]=1
		v[v2]=1
	avgx = sum(verts[i][0] for i in v.keys())/float(len(v))
	avgy = sum(verts[i][1] for i in v.keys())/float(len(v))
	avgz = sum(verts[i][2] for i in v.keys())/float(len(v))
	newvertex = (avgx,avgy,avgz)
	faces = [ (len(verts),e[0],e[1]) for e in edgeloop]
	return ([newvertex],faces)

def bounding_box(verts):
	maxx = max(v[0] for v in verts)
	minx = min(v[0] for v in verts)
	maxy = max(v[1] for v in verts)
	miny = min(v[1] for v in verts)
	maxz = max(v[2] for v in verts)
	minz = min(v[2] for v in verts)
	return ((minx,maxx),(miny,maxy),(minz,maxz))

def center(verts):
	n=len(verts)
	return (sum(v.co[0] for v in verts)/n,sum(v.co[1] for v in verts)/n,sum(v.co[2] for v in verts)/n)

def extract(verts,faces,vgroup,edgeloops=[]):
	verts = [ verts[i] for i in vgroup]
	mapverts = dict([(t[1],t[0]) for t in enumerate(vgroup)])
	faces = [ f for f in faces if all(i in vgroup for i in f)]
	faces = [ tuple(mapverts[i] for i in f) for f in faces]
	eloops = []
	for edgeloop in edgeloops:
		eloops.append([(mapverts[e[0]],mapverts[e[1]]) for e in edgeloop])
	return verts,faces,eloops

def flip(name):
	if name.endswith('.L'):
		return name[:-2]+'.R'
	elif name.endswith('.R'):
		return name[:-2]+'.L'
	return name
	
def newmesh(verts,faces,name=None):
	me=Blender.Mesh.New('Mesh')
	me.verts.extend(verts)
	me.faces.extend(faces)
	if name : me.name=name
	return me
		
def addmeshduplicate(scn,me,name=None):	
	ob=scn.objects.new(me)
	if name : ob.setName(name)
	
	# a newly added object is selected but not active, so we make it so
	scn.objects.active=ob
	# remDoubles() and recalcNormals() can only be done on meshes that are
	# embedded in a Blender Object!	
	# remove overlapping vertices
	me.remDoubles(0.001)
	
	# make all normals point to the outside	
	me.recalcNormals()
	
	# set the smooth attribute for all faces
	for f in me.faces: f.smooth = 1
	
	me.update()
	
	Blender.Window.RedrawAll()
	
	return ob

def addmeshobject(scn,verts,faces,name=None):
	me=newmesh(verts,faces,name)
	return addmeshduplicate(scn,me,name)

def addmodifiertoselected(scn,modifier=Blender.Modifier.Types.SUBSURF,settings={Blender.Modifier.Settings.LEVELS:2}):
	for ob in scn.objects.selected:
		mod=ob.modifiers.append(modifier)
		# a modifier does not support the update method :-(
		# mod.update(settings)
		for k,v in settings.items():
			mod[k]=v
		if ob.getType()=='Mesh':
			me=ob.getData(mesh=True)
			me.update()
	Blender.Window.RedrawAll()

menu=Blender.Draw.Create(1)

def DrawTreeMenu(menu_entries):
	charwidth=12
	charheight=20
	x=100
	y=40
	menu_string = ""
	t=0
	if menu_entries[0][0].endswith('%t'):
		menu_string = menu_entries[0][0]+'|'
		t=1
		
	menu_string += "|".join([n+"%x"+str(i) for n,i in menu_entries[t:]])
	global menu
	width=charwidth*max([len(s) for s,i in menu_entries])
	menu=Blender.Draw.Menu(menu_string, 1, x,y, 
		width, 
		charheight, menu.val, "Modifier to add to all selected objects")
	Blender.Draw.Label("Modifier to add", x, y+charheight, width, charheight)
	
def DTM_event(evt, val):
	if evt == Blender.Draw.ESCKEY:
		Blender.Draw.Exit()

def DTM_button_event(evt):
	if evt == 1:
		Blender.Draw.Exit()

	
def PupTreeMenu(menu_entries):
	global menu
	
	Blender.Draw.Register(lambda:DrawTreeMenu(menu_entries),DTM_event,DTM_button_event)
	
	return menu.val
	return -1
	