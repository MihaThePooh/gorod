"""Reference-driven v5 garment surfaces and anatomical details; metres, front -Y."""
import bpy,math,bmesh
from mathutils import Vector

def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)

def build(materials,pieces):
 def mesh(name,verts,faces,weights,mats,indices=None,sub=1):
  data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.validate();data.update()
  bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
  obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
  for m in mats:data.materials.append(materials[m])
  for i,p in enumerate(data.polygons):p.use_smooth=True;p.material_index=indices[i] if indices else 0
  for i,w in enumerate(weights):
   total=sum(w.values());assert total>0
   for bone,value in w.items():
    if value>1e-6:
     vg=obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone);vg.add([i],value/total,'REPLACE')
  if sub:
   obj['subdivision_levels']=sub
  pieces.append((obj,None));return obj
 def loft(name,rings,mats,bone,shape=.82,sub=1,matfn=None,weightfn=None,segments=48):
  if name in ('Head','Tailored jacket and vest'):
   dense=[]
   for lo,hi in zip(rings,rings[1:]):
    count=max(1,int(abs(hi[0]-lo[0])/.005))
    for k in range(count):dense.append(tuple(a+(b-a)*k/count for a,b in zip(lo,hi)))
   dense.append(rings[-1]);rings=dense
  v=[];w=[];f=[];mi=[]
  for i,(z,cx,cy,rx,ry) in enumerate(rings):
   for j in range(segments):
    a=j*math.tau/segments;co,si=math.cos(a),math.sin(a)
    x=cx+rx*math.copysign(abs(co)**shape,co);y=cy+ry*math.copysign(abs(si)**shape,si)
    # Localized cloth compression ridges follow diagonal tension lines.
    if name.startswith(('Trouser leg','Jacket sleeve','Tailored')):
     front=max(0,-si);back=max(0,si);d=0
     if name.startswith('Trouser leg'):
      side=-1 if 'L' in name else 1
      for height,amplitude,width,tilt in [(.30,.009,.013,.022),(.36,-.006,.018,-.028),(.43,.008,.014,.028),(.51,.010,.012,-.034),(.57,-.006,.018,.025),(.69,.005,.024,-.035),(.83,.007,.015,.035)]:
       q=(z-height-tilt*co*side)/width;d+=amplitude*math.exp(-q*q)*(front+.38*back)
      d+=.004*math.sin(5*a+z*8)*math.exp(-((z-.27)/.09)**2)
     elif name.startswith('Jacket sleeve'):
      for height,amp,tilt in [(1.06,.006,.018),(1.13,-.006,-.022),(1.18,.009,.018),(1.23,-.005,-.02),(1.32,.004,.025)]:
       d+=amp*math.exp(-((z-height-tilt*co)/.012)**2)
     else:
      d=.004*math.sin(5*a+z*7)*math.exp(-((z-1.10)/.09)**2)
      d+=.005*math.cos(a*7+.5)*math.exp(-((z-1.32)/.14)**2)*(front+.7*back)
     x+=co*d;y+=si*d
    if name=='Head' and si<0:
     # Brow ridge, eye sockets, cheek planes, muzzle, lips and chin.
     front=max(0,-si)**5
     g=lambda xx,zz,wx,wz:math.exp(-((x-xx)/wx)**2-((z-zz)/wz)**2)
     relief=0
     for eye_x in [-.042,.042]:
      relief+=.010*g(eye_x,1.706,.033,.013)-.009*g(eye_x,1.684,.025,.013)
      relief+=.009*g(eye_x*1.4,1.654,.032,.018)
     relief+=.008*g(0,1.617,.045,.015)+.008*g(0,1.560,.045,.016)
     relief-=.006*g(0,1.592,.041,.006)
     y-=front*relief
    v.append((x,y,z));w.append(weightfn(i,j,(x,y,z)) if weightfn else {bone:1})
  for i in range(len(rings)-1):
   for j in range(segments):
    f.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j));mi.append(matfn(i,j) if matfn else 0)
  f.extend([tuple(reversed(range(segments))),tuple(range((len(rings)-1)*segments,len(rings)*segments))]);mi.extend([0,0])
  return mesh(name,v,f,w,mats,mi,sub)
 def tube(name,centers,radii,bone,mat,segments=12,sub=1):
  v=[];w=[];f=[]
  for i,(c,r) in enumerate(zip(centers,radii)):
   tangent=Vector(centers[min(i+1,len(centers)-1)])-Vector(centers[max(i-1,0)])
   tangent.normalize();reference=Vector((0,1,0))
   if abs(tangent.dot(reference))>.95:reference=Vector((1,0,0))
   u=tangent.cross(reference).normalized();vv=tangent.cross(u).normalized()
   for j in range(segments):
    a=j*math.tau/segments;p=Vector(c)+r*(u*math.cos(a)+vv*math.sin(a));v.append(tuple(p));w.append({bone:1})
  for i in range(len(centers)-1):
   for j in range(segments):f.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
  f.extend([tuple(reversed(range(segments))),tuple(range((len(centers)-1)*segments,len(centers)*segments))])
  return mesh(name,v,f,w,[mat],sub=sub)
 # A rounded, anatomically shaped jacket and vest share one continuous torso.
 torso=[(1.00,.178,.115),(1.015,.181,.12),(1.06,.185,.126),(1.10,.195,.133),(1.12,.201,.136),(1.145,.205,.138),(1.18,.212,.140),(1.20,.214,.141),(1.225,.217,.141),(1.27,.223,.143),(1.35,.234,.14),(1.41,.237,.135),(1.45,.221,.125),(1.49,.185,.108),(1.515,.095,.076),(1.525,.080,.067)]
 def torso_mat_unused(i,j):
  z=(torso[i][0]+torso[i+1][0])/2;a=(j+.5)*math.tau/24
  if z<1.035:return 2
  if math.sin(a)<-.85 and abs(math.cos(a))<.17 and z>1.23:return 2
  if 1.12<z<1.145 or 1.20<z<1.225:return 1
  if z>1.27 and z<1.45 and abs(math.sin(a))>.8 and .38<abs(math.cos(a))<.57:return 1
  return 0
 def torso_w(i,j,p):
  f=smooth((p[2]-1.005)/.16);return {'hips':1-f,'spine':f}
 loft('Tailored jacket and vest',[(z,0,0,rx,ry) for z,rx,ry in torso],['navy','silver','navy'],'spine',shape=.72,sub=2,matfn=lambda i,j:0,weightfn=torso_w)
 loft('Trouser seat',[(.875,0,.018,.075,.060),(.905,0,.015,.155,.10),(.94,0,.01,.214,.132),(1.01,0,0,.18,.12),(1.025,0,0,.175,.115)],['navy'],'hips',shape=.76,sub=2)
 loft('Canvas belt',[(1.0,0,0,.182,.123),(1.006,0,0,.187,.128),(1.035,0,0,.185,.127),(1.041,0,0,.18,.12)],['belt'],'hips',shape=.7,sub=1)
 # Elbow and knee rings are continuous surfaces, not separate joint primitives.
 for side,x in [('L',-.12),('R',.12)]:
  sign=-1 if side=='L' else 1
  for part,H,E,W,bones in [
   ('Trouser leg',(x,0,.94),(x,-.015,.54),(x,0,.15),('thigh.'+side,'shin.'+side,'hips')),
   ('Jacket sleeve',(sign*.18,0,1.49),(sign*.27,-.015,1.18),(sign*.28,-.055,.99),('upper_arm.'+side,'forearm.'+side,'spine'))]:
   leg=part=='Trouser leg';H,E,W=map(Vector,(H,E,W));split=(E-H).length/((E-H).length+(W-E).length)
   ts=sorted(set([i/64 for i in range(65)]+[0,.025,.08,.16,.25,.34,split-.09,split-.045,split,split+.045,split+.09,.72,.82,.90,.96,.99,1]))
   rings=[]
   for t in ts:
    c=H.lerp(E,t/split) if t<=split else E.lerp(W,(t-split)/(1-split))
    if leg:
     radius=.098-(.098-.078)*smooth(t/.5) if t<.5 else .082+.008*math.sin((t-.5)/.5*math.pi)-.014*smooth((t-.76)/.24)
     depth=radius*(1+.025*math.cos(t*32))
    else:
     radius=.089-(.089-.054)*t;depth=radius*(1+.025*math.sin(t*28))
    if not leg:radius*=.12+.88*smooth(t/.16)
    if t>.96:radius*=1.025
    radius*=1+.025*math.exp(-((t-split)/.12)**2)*math.sin((t-split)*45)
    rings.append((c.z,c.x,c.y,radius,depth))
   def weights(i,j,p,ts=ts,split=split,bones=bones,leg=leg):
    t=ts[i];ang=j*math.tau/48;bias=.018*(-math.sin(ang))
    lower=smooth((t-(split-.10+bias))/.20);parent=(1-smooth(t/.17))*(.55 if leg else .65)
    return {bones[0]:(1-lower)*(1-parent),bones[1]:lower*(1-parent),bones[2]:parent}
   def cloth_mat(i,j,ts=ts):return 0
   loft(part+' '+side,rings,['navy','navyLight'],bones[0],shape=.9,sub=2,weightfn=weights,matfn=cloth_mat)
  # Soft glove palm, four shaped fingers and a curved thumb.
  gx=sign*.28;gy=-.065
  loft('Glove palm '+side,[(.875,gx,gy,.040,.028),(.89,gx,gy,.059,.039),(.94,gx,gy,.058,.041),(.982,gx,gy,.047,.036),(1.005,gx,gy,.045,.034)],['glove'],'hand.'+side,shape=.82,sub=2)
  for f in range(4):
   fx=gx+(f-1.5)*.022;length=[.059,.072,.068,.052][f]
   tube('Glove finger '+side+str(f),[(fx,gy,.899),(fx,gy-.004,.875),(fx,gy-.014,.875-length*.65),(fx,gy-.025,.875-length)], [.013,.013,.012,.008], 'hand.'+side,'glove',sub=2)
  tube('Glove thumb '+side,[(gx-sign*.045,gy,.95),(gx-sign*.068,gy-.012,.925),(gx-sign*.065,gy-.045,.892)], [.024,.021,.015],'hand.'+side,'glove',sub=2)
  # Boot sole and upper use the same rounded footprint: no box sole.
  loft('Rounded boot sole '+side,[(.012,x,-.055,.082,.149),(.017,x,-.055,.096,.165),(.053,x,-.055,.096,.165),(.068,x,-.055,.090,.158),(.074,x,-.055,.085,.151)],['bootSole'],'foot.'+side,shape=.78,sub=2,segments=32)
  verts=[];faces=[];weights=[]
  stations=[(-.213,.018,.087),(-.201,.055,.115),(-.17,.082,.135),(-.12,.090,.15),(-.065,.084,.19),(0,.072,.245),(.06,.070,.235),(.101,.045,.16),(.112,.012,.10)]
  n=14
  for y,w,top in stations:
   for j in range(n):
    a=j*math.tau/n;co=math.cos(a);si=math.sin(a)
    z=.073+(top-.073)*max(0,si)**.7 if si>=0 else .073+.014*si
    verts.append((x+w*co,y,z));weights.append({'foot.'+side:1})
  for i in range(len(stations)-1):
   for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
  faces.extend([tuple(reversed(range(n))),tuple(range((len(stations)-1)*n,len(stations)*n))])
  mesh('Shaped leather boot '+side,verts,faces,weights,['boot'],sub=2)
  loft('Boot ankle collar '+side,[(.16,x,.015,.068,.073),(.19,x,.017,.071,.076),(.265,x,.022,.067,.068),(.282,x,.022,.064,.064)],['boot'],'foot.'+side,sub=2)
  for i in range(4):
   y=-.07+i*.026;z=.198+i*.018
   tube('Boot lace '+side+str(i),[(x-.041,y,z),(x,y-.006,z+.012),(x+.041,y,z)], [.006,.006,.006],'foot.'+side,'lace',segments=8,sub=1)
 # Neck, jaw and face are also shaped profiles rather than a full head ellipse.
 loft('Neck',[(1.48,0,.005,.062,.057),(1.53,0,0,.062,.06),(1.59,0,0,.065,.06)],['skin'],'head',sub=2)
 loft('Head',[(1.535,0,-.017,.045,.049),(1.55,0,-.013,.070,.064),(1.59,0,-.008,.092,.078),(1.65,0,0,.105,.09),(1.71,0,.005,.108,.097),(1.765,0,.014,.092,.09),(1.79,0,.018,.06,.06)],['skin'],'head',shape=.9,sub=2)
 loft('Nose bridge',[(1.633,0,-.119,.019,.016),(1.651,0,-.125,.022,.022),(1.669,0,-.114,.014,.015),(1.70,0,-.098,.010,.009)],['skin'],'head',sub=2,segments=12)
 for x in (-.111,.111):
  loft('Ear',[(1.62,x,.01,.012,.018),(1.65,x,0,.019,.025),(1.69,x,.01,.012,.019)],['skin'],'head',sub=2,segments=12)
 for x in (-.043,.043):
  loft('Eye',[(1.677,x,-.092,.010,.006),(1.687,x,-.095,.012,.007),(1.692,x,-.093,.009,.005)],['skin'],'head',sub=1,segments=12)
  tube('Soft eyebrow',[(x-.020,-.091,1.707),(x,-.095,1.714),(x+.02,-.09,1.708)],[.004,.005,.004],'head','hair',segments=8)
 tube('Mouth',[(-.025,-.087,1.606),(0,-.094,1.602),(.025,-.087,1.606)],[.002,.0025,.002],'head','hair',segments=8)
 # A real dome silhouette and rounded brim, rigidly attached to the head.
 dome=[]
 for i in range(10):
  a=(i+.2)/10*math.pi/2;dome.append((1.76+.13*math.cos(a),0,0,.145*math.sin(a),.137*math.sin(a)))
 loft('Hardhat dome',list(reversed(dome)),['orange'],'head',shape=1,sub=2,segments=32)
 loft('Hardhat brim',[(1.75,0,-.025,.163,.171),(1.758,0,-.025,.175,.185),(1.772,0,-.024,.173,.180),(1.780,0,-.02,.155,.160)],['orange'],'head',shape=.92,sub=2,segments=32)
 for x in (-.047,.047):
  tube('Hardhat rib',[(x,.10,1.82),(x,.045,1.87),(x,-.04,1.88),(x,-.105,1.83)], [.006,.008,.008,.006],'head','orange',segments=8)
 return pieces
