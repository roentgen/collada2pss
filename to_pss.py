##
# Collada of blender converter for PSSuite
#   converts the file to make usable on PSS BasicModel
#
# Copyright (C) 2012 m.fukasawa 
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# changes:
# May 12, 2012 ver 0.1 [Beta Release]
# May 15, 2012 fixed an axis-order to rotation of bone
#
import os
import re
from mathutils import *
import math
import xml.dom.minidom
from xml.dom.minidom import parse

def options (v):
    options.do_bind_shape = True
     

def load_matrix4x4(str) :
    ms = []
    for i in map(lambda x: x != '' and ms.append(float(x)), re.compile('\s').split(str)) : pass
    matricis = []
    count = len(ms) / 16
    matricis = []
    for i in range(int(count)):
        m = Matrix()
        m[0][0], m[1][0], m[2][0], m[3][0], m[0][1], m[1][1], m[2][1], m[3][1], m[0][2], m[1][2], m[2][2], m[3][2], m[0][3], m[1][3], m[2][3], m[3][3] = float(ms[0]), float(ms[1]), float(ms[2]), float(ms[3]), float(ms[4]), float(ms[5]), float(ms[6]), float(ms[7]), float(ms[8]), float(ms[9]), float(ms[10]), float(ms[11]), float(ms[12]), float(ms[13]), float(ms[14]), float(ms[15])
        m.transpose()
        matricis.append(m)
        ms = ms[16:]
    return matricis

def store_bone_transform(n, mat, trans, rot, scale):
    nt = dom.createElement('translate')
    nt.setAttribute('sid', 'location')
    nt.appendChild(dom.createTextNode(vec3_to_str(trans)))
    n.insertBefore(nt, mat)
    
    # PSS ModelConverter will only accept Z-Y-X axis ordering to rotate.
    # if X/Y/Z ordering will be passed, then ModelConverter.exe should produce a broken quaternion.
    # the nodes of order is Z, Y, Z, not X/Y/Z. the order MUST be used!
    nrz = dom.createElement('rotate')
    nrz.setAttribute('sid', 'rotateZ')
    nrz.appendChild(dom.createTextNode('0 0 1 %f' % rot[2]))
    n.insertBefore(nrz, mat)
    
    nry = dom.createElement('rotate')
    nry.setAttribute('sid', 'rotateY')
    nry.appendChild(dom.createTextNode('0 1 0 %f' % rot[1]))
    n.insertBefore(nry, mat)

    nrx = dom.createElement('rotate')
    nrx.setAttribute('sid', 'rotateX')
    nrx.appendChild(dom.createTextNode('1 0 0 %f' % rot[0]))
    n.insertBefore(nrx, mat)
    
    ns = dom.createElement('scale')
    ns.setAttribute('sid', 'scale')
    ns.appendChild(dom.createTextNode(vec3_to_str(scale)))

# DOM query: by CSS selector

class RuleParser:

    def parse(self, str):
        r = re.compile('[     　]+|\+|>|,|[\.#&_\-a-zA-Z0-9%:]+|\[|\]|~=|\|=|=|\"|\'|\*|\\\\')
        e = re.compile('[ 	　]+')
        elm = re.compile('[a-zA-Z0-9:\*\.#]+')
        matchs = iter(r.findall(str))
        expset = []
        explst = []
        tag = ''
        
        for m in matchs:
            if e.match(m):
                # decendant
#                if tag != '':
#                    explst.append({'rel':'', 'left':tag, 'right':None})
#                    tag = ''
                continue
            elif m == '>':
                # child
                for mm in matchs:
                    if elm.match(mm):
                        if tag != '':
                            explst.append(self.splittag(tag))
                        explst.append({'rel':'>', 'left':None, 'right':None})
                        explst.append(self.splittag(mm))
                        tag = ''
                        break
                continue
            elif m == '+':
                # sibling
                for mm in matchs:
                    if elm.match(mm):
                        if tag != '':
                            explst.append(self.splittag(tag))
                        explst.append({'rel':'+', 'left':None, 'right':mm})
                        explst.append(self.splittag(mm))
                        tag = ''
                        break
                continue
            elif m == ',':
                # camma
                if tag != '':
                    explst.append(self.splittag(tag))
                    tag = ''
                expset.append(explst)
                explst = []
            elif m == '[':
                # attribute [attr[~|]=val]
                key = kexp = ''
                for mm in matchs:
                    if e.match(mm):
                        continue
                    key = mm
                    break
                for mm in matchs:
                    if e.match(mm):
                        continue
                    kexp = mm
                    break
                if kexp == ']':
                    if tag != '':
                        explst.append(self.splittag(tag))
                        explst.append({'rel':'*=', 'left':key, 'right':None}) # has attr
                        tag = ''
                        continue

                value = ''
                esclevel = []
                for mm in matchs:
                    if len(esclevel) == 0:
                        if mm == ']':
                            break
                        if mm == '"':
                            esclevel.append('"')
                            continue
                        if mm == '\'':
                            esclevel.append('\'')
                            continue
                        value = value + mm
                        if mm == '\\':
                            value = value + matchs.next()
                    else:
                        if esclevel[-1] == mm:
                            esclevel.pop()
                        else:
                            value = value + mm
                if tag != '':
                    explst.append(self.splittag(tag))
                value = value.strip()
                explst.append({'rel':kexp, 'left':key, 'right':value})
                tag = ''
                continue
            else:
                if tag != '':
                    explst.append(self.splittag(tag))
                    explst.append(self.splittag(m))
                    tag = ''
                else:
                    tag = m

        if tag != '':
            explst.append(self.splittag(tag))
        expset.append(explst)
        return expset

    def splittag(self, str, rel=''):
        s = str.split('.')
        if len(s) > 1:
            return {'rel':'.', 'left':s[0], 'right':s[1]}
        s = str.split('#')
        if len(s) > 1:
            return {'rel':'#', 'left':s[0], 'right':s[1]}
        return {'rel':rel, 'left':None, 'right':str}

def findAll_r(slf, res, elem, attrs={}, recursive=True):
    if elem != None:
#        els = slf.getElementsByTagName(elem)
        els = slf.childNodes
        if len(els) == 0 and recursive == True:
            els = slf.childNodes
    else:
        els = slf.childNodes
    for e in els:
        if e.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
            continue
#        print ("findAll_r child:", e)
        if elem == None:
            for (k, v) in attrs:
                if v == True and e.attributes[k] != None:
                    res.append(e)
                elif e.attributes[k].value == v:
                    res.append(e)
        elif e.tagName == elem:
#            print ("matched node:%(en)s find keys:%(a)s" % {'en':e.tagName, 'a':attrs})
            if len(attrs) == 0:
                res.append(e)
            else:
                for (k, v) in attrs:
                    if v == True and e.attributes[k] != None:
                        res.append(e)
                    elif e.attributes[k].value == v:
                        res.append(e)
        if recursive == True:
            findAll_r(e, res, elem, attrs, recursive)
        

def findAll(slf, elem, attrs={}, recursive=True):
    res = []
    if slf.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
        return res
#    print ("findAll: self: %s" % slf)
    findAll_r(slf, res, elem, attrs, recursive)
#    print ('findAll: resultset: res:', res)
    return res
    

def find_r(slf, res, elem, attrs={}, recursive=True):
    if len(res) != 0:
        return
    if elem != None:
        els = slf.getElementsByTagName(elem)
        if len(els) == 0 and recursive == True:
            els = slf.childNodes
    else:
        els = slf.childNodes
    for e in els:
        if e.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
            continue
        if elem == None:
            for (k, v) in attrs:
                if v == True and e.attributes[k] != None:
                    res.expand(e)
                    return
                elif e.attributes[k].value == v:
                    res.expand(e)
                    return
        elif e.tagName == elem:
#            print ("matched node:%(en)s find keys:%(a)s" % {'en':e.tagName, 'a':attrs})
            if len(attrs) == 0:
                res.expand(e)
                return
            for (k, v) in attrs:
                if v == True and e.attributes[k] != None:
                    res.expand(e)
                    return
                elif e.attributes[k].value == v:
                    res.expand(e)
                    return
            
        if recursive == True:
            find_r(e, res, elem, attrs, recursive)

def find(slf, elem, attrs={}, recursive=True):
    res = []
    if slf.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
        return res
    find_r(slf, res, elem, attrs, recursive)
    return res[0]

def findNextSibling(slf, elem, attrs={}):
    if slf.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
        return None
    r = slf.nextSibling;
    while r != None:
        elem_match = Flase
        if elem != None and r.tagName == elem:
            elem_match = True
        elif r.tagName == elem:
            elem_match = True
        if elem_match:
            for (k, v) in attrs:
                if v != None and r.attributes[k] != None:
                    return r
                if r.attributes[k].value == v:
                    return r
        r = r.nextSibling
    return None

def search(x, attr):
    if x.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
        return False
    k = list(attr.keys())[0]
#    print ('find key:%(k)s value:%(v)s %(e)s [%(a)s]' % {'k':k, 'v':attr[k], 'e':x, 'a':x.attributes})
    if x.hasAttribute(k) and x.attributes[k].value == attr[k]:
        return True
    return False

def binder(obj):
    def f() :
        pass
#    print("binder:", obj)
    f.inner = obj
    f.findAll = findAll
    f.find = find
    f.findNextSibling = findNextSibling
    f.search = search
    return f
    

def eval(dom, expset):
    resultset = []
    
    def inner_all(l, elem, attrs, rec): return lambda x: l.extend(binder(x).findAll(x, elem, attrs, recursive=rec))
    def inner_self_attr(l, attrs):      return lambda x: binder(x).search(x, attrs) and l.append(x)
    def inner_attr(l, attrs):           return lambda x: l.extend(binder(x).findAll(x, attrs=attrs, recursive=False))
    def inner(l, elem, attrs, rec):     return lambda x: l.append(binder(x).find(x, elem, attrs, recursive=rec))
    def inner_siblings(l, elem, attrs): return lambda x: l.extend(binder(x).findNextSiblings(x, elem, attrs))
    def inner_sibling(l, elem, attrs):  return lambda x: l.append(binder(x).findNextSibling(x, elem, attrs))

    for explst in expset:
        it = iter(explst)
        l = []
        r = dom.childNodes
        for exp in it:
            rel = exp['rel']
#            print ('rel:%(rel)s r:%(count)d' % {'rel':rel, 'count':len(r)})
            l = []
            mo = None
            if rel == '':
                mo = map(inner_all(l, exp['right'], {}, True), r)
            elif rel == '.':
#                logging.info('EXPRESSION: %s', (r'\b' + re.escape(exp['right']) + r'\b'))
                mo = map(inner_all(l, exp['left'], {'class': re.compile(r'\b' + re.escape(exp['right']) + r'\b')}, True), r)
#            map(inner_all(l, exp['left'], {'class': exp['right']}, True), r)
            elif rel == '#':
                mo = map(inner(l, exp['left'], {'id': exp['right']}, True), r)
            elif rel == '>':
                exp = next(it)
                if exp['rel'] == '': mo = map(inner_all(l, exp['right'], {}, False), r)
                if exp['rel'] == '.': mo = map(inner_all(l, exp['left'], {'class': exp['right']}, False), r)
                if exp['rel'] == '#': mo = map(inner(l, exp['left'], {'id': exp['right']}, False), r)
                if exp['rel'] == '=': 
                    mo = map(inner_self_attr(l, attrs={exp['left']:exp['right']}), r)
                if exp['rel'] == '*=': 
                    mo = map(inner_self_attr(l, attrs={exp['left']:True}), r)
            elif rel == '+':
                exp = next(it)
                if exp['rel'] == '': mo = map(inner_sibling(l, exp['right'], {}), r)
                if exp['rel'] == '.': mo = map(inner_sibling(l, exp['left'], {'class': exp['right']}), r)
                if exp['rel'] == '#': mo = map(inner_sibling(l, exp['left'], {'id': exp['right']}), r)
                if exp['rel'] == '=': 
                    mo = map(inner_self_attr(l, attrs={exp['left']:exp['right']}), r)
                if exp['rel'] == '*=': 
                    mo = map(inner_self_attr(l, attrs={exp['left']:True}), r)
                
            elif rel == '=':
                # x.find(attrs={}) does not find x self
                mo = map(inner_self_attr(l, attrs={exp['left']:exp['right']}), r)
            elif rel == '*=':
                mo = map(inner_self_attr(l, attrs={exp['left']:True}), r)
            if mo: [m for m in mo]
                
            r = [i for i in l if i is not None]
        resultset.extend(r)
    return resultset

def do_recipe(recipes, root):
    for r in recipes:
#        print (r['rule'])

        rp = RuleParser()
        expr = rp.parse(r['rule'])
#        print (expr)
        set = eval(root, expr)
#        print (set)
        for s in set:
            r['func'](s)

def document_fix(dom):

    # whenever Blender2.63 provides instance_controller node despite no controllers. fix it.
    ctrls = dom.getElementsByTagName('controller')
    ics = dom.getElementsByTagName('instance_controller')
    for c in ics:
        url = c.attributes['url'].value
        ids = re.compile('[# ]+').split(url)
        for i in ids:
            if i == '': continue
            match = False
            for cdef in ctrls:
                if cdef.attributes['id'].value == i:
                    match = True
                    break
            if match == False:
                print ('Warning: instance_controller[id=%s] is not defined in a library_controllers section. create an instance_geometry' % i)
                g = dom.createElement('instance_geometry')
                g.setAttribute('url', '#%s' % url)
                par = c.parentNode
                par.replaceChild(g, c)
                
    # PSS Beta may not accept some image formats. warn it
    images = dom.getElementsByTagName('image')
    for i in images:
        files = i.getElementsByTagName('init_from')
        for f in files:
            fname = f.childNodes[0].nodeValue.lower()
            if fname[-3:] != 'jpg' and fname[-4:] != 'jpeg' and fname[-3:] != 'png' and fname[-3:] != 'bmp' and fname[-3:] != 'gif':
                print ('Warning: image file %s may not be support on PSS' % fname)
    
    # PSS Beta BasicModel: a mesh must have at least one material 
    # check all meshes if it has a material
    polys = []
    recipes = [{'rule':'polylist', 'func':lambda x: polys.append(x)}]
    do_recipe(recipes, dom.getElementsByTagName('library_geometries')[0])
    for p in polys:
        if not p.hasAttribute('material'):
            p.setAttribute('material', 'Material0')

    meshes = []
    recipes = [{'rule':'instance_controller', 'func':lambda x: meshes.append(x)}, {'rule':'instance_geometry', 'func':lambda x: meshes.append(x)}]
    do_recipe(recipes, dom.getElementsByTagName('visual_scene')[0])
    need_dummy_material = False
    for m in meshes:
        mats = m.getElementsByTagName('bind_material')
        if len(mats) == 0:
            print('Warning: found instance_controller/geometry[url=%s] has no any material. bind to dummy material' % m.attributes['url'].value)
            need_dummy_material = True
            inst_mat = dom.createElement('instance_material')
            inst_mat.setAttribute('symbol', 'Material0')
            inst_mat.setAttribute('target', '#dummy_material')
            tec = dom.createElement('technique_common')
            tec.appendChild(inst_mat)
            bindmat = dom.createElement('bind_material')
            bindmat.appendChild(tec)
            m.appendChild(bindmat)

            

    if need_dummy_material:
        print('Warning: create dummy material')
        libmats = dom.getElementsByTagName('library_materials')
        if len(libmats) == 0 :
            libmat = dom.createElement('library_materials')
            dom.getElementsByTagName('COLLADA')[0].appendChild(libmat)
        else:
            libmat = libmats[0]
        mat = dom.createElement('material')
        mat.setAttribute('id', 'dummy_material')
        mat.setAttribute('name', 'dummy_material')
        insfx = dom.createElement('instance_effect')
        insfx.setAttribute('url', '#dummy_material-fx')
        mat.appendChild(insfx)
        libmat.appendChild(mat)

        # create dummy material and effect as lambert
        mat = dom.createElement('material')
        mat.setAttribute('id', 'dummy_material')
        mat.setAttribute('name', 'dummy_material')
        ie = dom.createElement('instance_effect')
        ie.setAttribute('url', '#dummy_material-fx')
        
        lambert = dom.createElement('lambert')
        diffuse = dom.createElement('diffuse')
        color = dom.createElement('color')
        color.appendChild(dom.createTextNode('0.7 0.7 0.7 1.0'))
        diffuse.appendChild(color)
        lambert.appendChild(diffuse)
        tec = dom.createElement('technique')
        tec.setAttribute('sid', 'common')
        tec.appendChild(lambert)
        
        fx = dom.createElement('effect')
        fx.setAttribute('id', 'dummy_material-fx')
        pcommon = dom.createElement('profile_COMMON')
        pcommon.appendChild(tec)
        fx.appendChild(pcommon)
        libfxs = dom.getElementsByTagName('library_effects')
        if len(libfxs) == 0 :
            libfx = dom.createElement('library_effects')
            dom.getElementsByTagName('COLLADA')[0].appendChild(libfx)
        else:
            libfx = libfxs[0]
        libfx.appendChild(fx)
            

version = 0.1
argv_ = re.compile('[# ]+').split(os.getenv('args'))
argv = []
for i in argv_:
    if i != '':
        argv.append(i)

print(argv)
argc = len(argv)

if (argc < 2):
    print('to_pss usage: %s input output' % argv[0])
    exit()

options(argv)

infile = argv[0]
outfile = argv[1]

def vec3_to_str(v):
    return '%(x)f %(y)f %(z)f' % {'x':v[0], 'y':v[1], 'z':v[2]}

def store_matrix4x4(m):
    c = len(m)
    s = ''
    for i in range(c):
        mat = m[i]
        mat.transpose()
        s += '%(m00)f %(m10)f %(m20)f %(m30)f %(m01)f %(m11)f %(m21)f %(m31)f %(m02)f %(m12)f %(m22)f %(m32)f %(m03)f %(m13)f %(m23)f %(m33)f \n' % \
        {'m00':mat[0][0], 'm10':mat[1][0], 'm20':mat[2][0], 'm30':mat[3][0], \
         'm01':mat[0][1], 'm11':mat[1][1], 'm21':mat[2][1], 'm31':mat[3][1], \
         'm02':mat[0][2], 'm12':mat[1][2], 'm22':mat[2][2], 'm32':mat[3][2], \
         'm03':mat[0][3], 'm13':mat[1][3], 'm23':mat[2][3], 'm33':mat[3][3]}
    return s

def traverse_node(n):
    if (n.nodeType != xml.dom.minidom.Node.ELEMENT_NODE):
        return
    if (n.tagName == 'node' and n.attributes['type'].value == "JOINT"):
        joint_handler(n)
    nodes = n.childNodes
    for n in nodes:
        traverse_node(n)

def traverse(first_tag):
    root = dom.getElementsByTagName(first_tag)[0]
    nodes = root.childNodes
    for n in nodes:
        traverse_node(n)

def joint_handler (n) :
    print ('found joint: id:', n.attributes['id'].value)
    mat = n.getElementsByTagName("matrix")[0]
#    print ('found joint matrix %s' % mat.firstChild.nodeValue)
    m = load_matrix4x4(mat.firstChild.nodeValue)[0]
    trans = m.to_translation()
    scale = m.to_scale()
    floats = m.to_euler('XYZ')
    rot = []
    for f in floats:
        rot.append(math.degrees(f))

    store_bone_transform(n, mat, trans, rot, scale)
    n.removeChild(mat)

def store_single_channel_source(id, data, tag='-output', param_name='ANGLE', param_type='float', stride='1'):
    srcbase = srcid[:id.rfind('_')]
    count = len(data)
    id = srcbase + tag

#    print ('id:', id)

    src = dom.createElement('source')
    src.setAttribute('id', id)
    farray = dom.createElement('float_array')
    farray.setAttribute('id', id + '-array')
    farray.setAttribute('count', '%d' % count)

    def f():
        def concat(x):
            concat.str = concat.str + '%f ' % x
            return concat.str
        concat.str = ''
        return concat
    con = f()
    for m in map(con, data): pass
    str = con.str
    str = str.rstrip(' ')
    farray.appendChild(dom.createTextNode(str))

    src.appendChild(farray)
    acc = dom.createElement('accessor')
    acc.setAttribute('source', '#' + id + '-array')
    acc.setAttribute('count', '%d' % count)
    acc.setAttribute('stride', stride)

    if param_name == 'XYZ':
        param = dom.createElement('param')
        param.setAttribute('name', 'X')
        param.setAttribute('type', 'float')
        acc.appendChild(param)
        param = dom.createElement('param')
        param.setAttribute('name', 'Y')
        param.setAttribute('type', 'float')
        acc.appendChild(param)
        param = dom.createElement('param')
        param.setAttribute('name', 'Z')
        param.setAttribute('type', 'float')
        acc.appendChild(param)
    else:
        param = dom.createElement('param')
        param.setAttribute('name', param_name)
        param.setAttribute('type', param_type)
        acc.appendChild(param)
    
#    print('acc:', acc.toprettyxml())
    tec = dom.createElement('technique_common')
    tec.appendChild(acc)
    src.appendChild(tec)
    return src
   
def store_single_channel_animation(id, org, data, tag='_rotateX', param_name='ANGLE', param_type='float'):
    srcbase = id[:id.rfind('_')]
    anim = dom.createElement('animation')
    anim.setAttribute('id', srcbase + tag)

#    print ('id:', srcbase + tag)

    stride = '1'
    if param_type == 'float':
        stride = '1'
    elif param_type == 'float' and param_name == 'XYZ':
        stride = '3'
    elif param_type == 'float4x4':
        stride = '16'
    # copy input source
    input_org = []
    interp_org = []
#    recipes = [{'rule':'source[id=%(id)s] > float_array' % {'id':id+'-input'}, 'func':lambda x: input_org.append(x)},
#               {'rule':'source[id=%(id)s] > Name_array' % {'id':id+'-interpolation'}, 'func':lambda x: interp_org.append(x)}]

    print ('srcid tag:%(id)s base:%(base)s' % {'id':srcbase + tag, 'base':srcbase})
    recipes = [{'rule':'float_array[id=%(id)s]' % {'id':srcbase+'_matrix-input-array'}, 'func':lambda x: input_org.append(x)},
               {'rule':'Name_array[id=%(id)s]' % {'id':srcbase+'_matrix-interpolation-array'}, 'func':lambda x: interp_org.append(x)}]
    do_recipe(recipes, org)
    input_org = input_org[0]
    interp_org = interp_org[0]
## WTF, getElementById() does not work
#    input_org = dom.getElementById(id + '-input').getElementsByTagName('float_array')[0]
#    interp_org = dom.getElementById(id + '-interpolation').getElementsByTagName('Name_array')[0]
    input = dom.createElement('source')
    input.setAttribute('id', srcbase + tag + '-input')
    float_array = dom.createElement('float_array')
    float_array.setAttribute('id', srcbase + tag + '-input-array')
    float_array.setAttribute('count', input_org.attributes['count'].value)
    float_array.appendChild(dom.createTextNode(input_org.childNodes[0].nodeValue))
    input.appendChild(dom.createTextNode('\n'))
    input.appendChild(float_array)
    input.appendChild(dom.createTextNode('\n'))

    accessor = dom.createElement('accessor')
    accessor.setAttribute('source', '#' + srcbase + tag + '-input-array')
    accessor.setAttribute('count', input_org.attributes['count'].value)
    accessor.setAttribute('stride', '1')

    param = dom.createElement('param')
    param.setAttribute('name', 'TIME')
    param.setAttribute('type', 'float')
    accessor.appendChild(param)
    tec = dom.createElement('technique_common')
    tec.appendChild(accessor)
    input.appendChild(tec)
    anim.appendChild(input)
    anim.appendChild(dom.createTextNode('\n'))

    out = store_single_channel_source(id, data, tag=tag+'-output', param_name=param_name, stride=stride)
    anim.appendChild(dom.createTextNode('\n'))
    anim.appendChild(out)
    anim.appendChild(dom.createTextNode('\n'))
    
#    print ('output:', anim.toprettyxml())

    #interpolation
    interp = dom.createElement('source')
    interp.setAttribute('id', srcbase + tag + '-interpolation')
    name_array = dom.createElement('Name_array')
    name_array.setAttribute('id', srcbase + tag + '-interpolation-array')
    name_array.setAttribute('count', interp_org.attributes['count'].value)
    name_array.appendChild(dom.createTextNode(interp_org.childNodes[0].nodeValue))
    interp.appendChild(name_array)
    accessor = dom.createElement('accessor')
    accessor.setAttribute('source', '#' + srcbase + tag + '-interpolation-array')
    accessor.setAttribute('count', interp_org.attributes['count'].value)
    accessor.setAttribute('stride', '1')
    param = dom.createElement('param')
    param.setAttribute('name', 'INTERPOLATION')
    param.setAttribute('type', 'name')
    accessor.appendChild(param)
    tec = dom.createElement('technique_common')
    tec.appendChild(accessor)
    interp.appendChild(tec)
    anim.appendChild(dom.createTextNode('\n'))
    anim.appendChild(interp)
    anim.appendChild(dom.createTextNode('\n'))

    # sampler
    sampler = dom.createElement('sampler')
    sampler.setAttribute('id', srcbase + tag + '-sampler')
    sem = dom.createElement('input')
    sem.setAttribute('semantic', 'INPUT')
    sem.setAttribute('source', '#' + srcbase + tag + '-input')
    sampler.appendChild(sem)
    sem = dom.createElement('input')
    sem.setAttribute('semantic', 'OUTPUT')
    sem.setAttribute('source', '#' + srcbase + tag + '-output')
    sampler.appendChild(sem)
    sem = dom.createElement('input')
    sem.setAttribute('semantic', 'INTERPOLATION')
    sem.setAttribute('source', '#' + srcbase + tag + '-interpolation')
    sampler.appendChild(sem)
    anim.appendChild(sampler)
    anim.appendChild(dom.createTextNode('\n'))

#    print ('sema:', anim.toprettyxml())

    # channel
    channel = dom.createElement('channel')
    channel.setAttribute('source', '#' + srcbase + tag + '-sampler')
    target = org.getElementsByTagName('channel')[0].attributes['target'].value
    target = target[:target.find('/')]

    if tag == '_rotateX':
        channeltag = 'rotateX.ANGLE'
#        channeltag = 'rotateZ.ANGLE'
    elif tag == '_rotateY':
        channeltag = 'rotateY.ANGLE'
    elif tag == '_rotateZ':
        channeltag = 'rotateZ.ANGLE'
#        channeltag = 'rotateX.ANGLE'
    elif tag == '_translate':
        channeltag = 'translate'
    elif tag == '_scale':
        channeltag = 'scale'
#    print ('target:', target + '/' + channeltag)
    channel.setAttribute('target', target + '/' + channeltag)
    anim.appendChild(channel)
    input.appendChild(dom.createTextNode('\n'))

#    print ('last:', anim.toprettyxml())
    return anim

# controllers: dictionaly of controllers which have skeleton
controllers = {}
def controller_handler(c):
    id = c.attributes['id'].value
    controller = controllers.get(id)
    # ignore if the controller does not have a skeleton
    print ('controller_handler: id:', id)
    print ('controller_handler: controller:', controller)
    if controller == None:
        return  
    controller.bind_shape_matrix = Matrix.Identity(4)
    binds = c.getElementsByTagName('bind_shape_matrix')
    if len(binds) : 
        m = load_matrix4x4(binds[0].childNodes[0].nodeValue)[0]
        # strip scale element
        scale = m.inverted().decompose()[2]
        inv_scale = Matrix.Identity(4)
        inv_scale[0][0] = scale[0]
        inv_scale[1][1] = scale[1]
        inv_scale[2][2] = scale[2]
        m = inv_scale * m
        controller.bind_shape_matrix = m
    
    # get bone name array
    controller.bone_names = []
    name_array_nodelist = c.getElementsByTagName('Name_array')
    print ('name_array:', name_array_nodelist)
    if len(name_array_nodelist):
        nms = re.compile('\s').split(name_array_nodelist[0].childNodes[0].nodeValue)
        for n in nms:
            if n != '':
                controller.bone_names.append(n)

    # find pose matricis to be use as bone-offset-matricis
    poses = []
    recipes = [{'rule':'input[semantic=INV_BIND_MATRIX]', 'func': lambda x: poses.append(x.attributes['source'].value.strip('#'))}]
    do_recipe(recipes, c)
    boneoffsets = []
    for p in poses:
        recipes = [{'rule':'source[id=%s] float_array' % p, 'func': lambda x: boneoffsets.append(x)}]
        do_recipe(recipes, c)
    if len(boneoffsets) == 0:
        return
    matricis = load_matrix4x4(boneoffsets[0].childNodes[0].nodeValue)

    idx = 0
    for b in controller.bone_names:
        print ('bonename:', b)
#        def add_rot90x(x):
#            (v, q, s) = x.decompose()
##            rot90 = Matrix.Rotation(math.radians(-90), 4, 'X')
#            rot90 = Matrix() # dry run
#            return Matrix.Translation(v) * q.to_matrix().to_4x4() * rot90

        # name_array is name ? or id ?
        name = b
        # lookup parent of 'name'
#        parents = []
#        recipes = [{'rule':'node [id=%s]' % name, 'func': lambda x: parents.append(x.parentNode)}]
#        do_recipe(recipes, controller.skeleton_root)
#        parent = parents[0]
#        # resolve parent index
#        parent_idx = -1
#        if parent:
#            parent_name = parent.attributes['id'].value
#            pidx = 0
#            for n in controller.bone_names:
#                if n == parent_name:
#                    parent_idx = pidx
#                    break
#                pidx += 1
#            print ('parent id:%(id)s idx:%(idx)d' % {'id':parent.attributes['id'].value, 'idx':parent_idx}) 
#        else:
#            print ('Error: controller:%s: skeleton-root does not found' % id)

#        print ('cur: %(a)d parent:%(b)d' % {'a':idx, 'b':parent_idx})
#        print ('prev:', matricis[idx])
#        if parent_idx != -1:
#            lm = matricis[parent_idx] * matricis[idx].inverted()
#            matricis[idx] = *matricis[parent_idx] * add_rot90x(lm)).inverted()
#        else:
#            lm = matricis[idx].inverted()
#            matricis[idx] = add_rot90x(lm).inverted()
        im = matricis[idx].inverted()
        matricis[idx] = (Matrix.Rotation(math.radians(-90), 4, 'X') * im).inverted()
#        print ('aftr:', matricis[idx])
        idx += 1
    boneoffsets[0].childNodes[0].nodeValue = store_matrix4x4(matricis)

#    print('bind_shape_matrix:\n', controller.bind_shape_matrix)
#    inv_binds = controller.bind_shape_matrix.inverted()
#    for b in boneoffsets:
#        matricis.extend(load_matrix4x4(b.childNodes[0].nodeValue))
#        num = len(matricis)
#        for i in range(num):
#            # fixed matrix that converts a local system to the world system.
#            #      matrix = bind^-1 * pose * bone
#            # multiplying each bone local matrix will be done runtime.
#            print ('pose:\n', matricis[i])
#            matricis[i] = matricis[i] * inv_scale
#            print ('inv_binds:\n', inv_binds)
#            print ('matrix:\n', matricis[i])
#        b.childNodes[0].nodeValue = store_matrix4x4(matricis)
        
    return 
    

dom = parse(infile)


# fix document errors
document_fix(dom)

# if Z_UP, then add the node that makes the axis Y_UP
if dom.getElementsByTagName('asset')[0].getElementsByTagName('up_axis')[0].childNodes[0].nodeValue == 'Z_UP':
    armatures = []
    recipes = [{'rule':'visual_scene > node[type=NODE] > node[type=JOINT]', 'func':lambda x: armatures.append(x.parentNode)}]
    do_recipe(recipes, dom)
    for a in armatures:
        p = a.parentNode
        id = '__axis__' + a.attributes['id'].value
        r = dom.createElement('node');
        r.setAttribute('type', 'NODE')
        r.setAttribute('id', id)
        rot = dom.createElement('rotate')
        rot.setAttribute('sid', 'rotateX')
        rot.appendChild(dom.createTextNode('1 0 0 -90'))
        r.appendChild(rot)
        r.appendChild(dom.createTextNode('\n'))
        p.replaceChild(r, a)
        r.appendChild(a)

# makes a map of controller and bone
controller_instances = []
recipes = [{'rule':'instance_controller', 'func':lambda x: controller_instances.append(x)}]
do_recipe(recipes, dom)
for c in controller_instances:
    
    def controller():
        pass

    id = c.attributes['url'].value.strip('#')
    controller.id = id
    # instance_controller may have many skeleton nodes, but blender's has only root node
    skeletons = c.getElementsByTagName('skeleton')
    if len(skeletons):
        skeleton = skeletons[-1]
        skeleton_id = skeleton.childNodes[0].nodeValue.strip('#')
        controller.skeleton_id = skeleton_id
    else:
        controller.skeleton_id = None
        controller.skeleton_root = None
    if controller.skeleton_id != None:
        # find skeleton root
        skels = []

#        print ('skeleton id:', controller.skeleton_id)
        recipes = [{'rule':'node[id=%s]' % controller.skeleton_id, 'func':lambda x: skels.append(x)}]
        do_recipe(recipes, dom)
        if len(skels) == 0:
            print ('Error: skeleton was used but not defined: Did not you export collada in wrong layer? Blender may do not export objects in other layers.')

        for s in skels:
            p = s.parentNode
            skeleton_root = None
            while p.tagName == 'node':
                skeleton_root = p
                p = p.parentNode
            controller.skeleton_root = skeleton_root
        print('controller instance: id:', id)
        print('controller instance: skelton:', controller.skeleton_id)
        controllers.update({id:controller})


if options.do_bind_shape:
    ctrls = []
    recipes = [{'rule':'controller', 'func':lambda x: ctrls.append(x)}]
    do_recipe(recipes, dom)
    for i in map(controller_handler, ctrls): pass

# convert bone matrix
vs = dom.getElementsByTagName('visual_scene')[0]
recipes = [{'rule':'node[type=JOINT]', 'func':joint_handler}]
do_recipe(recipes, vs)

# traverse('visual_scene')



# convert animation matrix 
libanims = dom.getElementsByTagName('library_animations')
if len(libanims):
    print('convert animation matricis')
    libanim = libanims[0]
    anims = []
    new_anims = []
    recipes = [{'rule':'animation', 'func':lambda x: anims.append(x)}]
    do_recipe(recipes, dom)
#    print(anims)
    for anim in anims:
        # RNA data path bpy.data.objects['Armature'].pose.bones['Bone.001'].rotation_quaternion
        # how to eval a channel value: bpy.data.actions['ArmatureAction'].fcurves[13].evaluate(frame)
        srcs = []
        recipes = [{'rule':'accessor > param[type=float4x4]', 'func':lambda x: srcs.append(x.parentNode)}]
        do_recipe(recipes, anim)
        for src in srcs:
            print('matched motion data:%s' % src.attributes['source'])
            srcid = src.attributes['source'].value
            count = src.attributes['count'].value
            stride = src.attributes['stride'].value

            srcid = srcid.strip('#')
#            print (srcid)
            # wtf, getElementById does not work
            #matricis = load_matrix4x4(dom.getElementById(srcid).nodeValue)
            matricis = load_matrix4x4(src.parentNode.parentNode.getElementsByTagName('float_array')[0].firstChild.nodeValue)
            floats_rad = []
            for m in matricis:
                floats_rad.extend(m.to_euler('XYZ'))
            floats = []
            for f in floats_rad:
                floats.append(math.degrees(f))

            # rotateZ channel
            data = []
            for i in range(len(floats)):
                if i % 3 == 2: data.append(floats[i])
            anim_rz = store_single_channel_animation(srcid, anim, data, tag='_rotateZ', param_name='ANGLE')
            new_anims.append(anim_rz)

            # rotateY channel
            data = []
            for i in range(len(floats)):
                if i % 3 == 1: data.append(floats[i])
            anim_ry = store_single_channel_animation(srcid, anim, data, tag='_rotateY', param_name='ANGLE')
            new_anims.append(anim_ry)

            # rotateX channel
            data = []
            for i in range(len(floats)):
                if i % 3 == 0: data.append(floats[i])
            anim_rx = store_single_channel_animation(srcid, anim, data, tag='_rotateX', param_name='ANGLE')
            new_anims.append(anim_rx)

            # translateX/Y/Z channel
            floats = []
            for m in matricis:
                floats.extend(m.to_translation())

            anim_t = store_single_channel_animation(srcid, anim, floats, tag='_translate', param_name='XYZ')
            new_anims.append(anim_t)

            # scale channel
            floats = []
            for m in matricis:
                floats.extend(m.to_scale())
            anim_s = store_single_channel_animation(srcid, anim, floats, tag='_scale', param_name='XYZ')
            new_anims.append(anim_s)
        
            # remove old animation
            libanim.removeChild(anim)

    for a in new_anims:
        libanim.appendChild(a)
        libanim.appendChild(dom.createTextNode('\n\n'))

out = open(outfile, 'w')
#out.write(dom.toprettyxml())
dom.writexml(out)
out.close()

dom.unlink()
